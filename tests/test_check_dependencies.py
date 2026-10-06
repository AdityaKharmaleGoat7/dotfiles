"""Dependency diagnostics: isolated files and deterministic installed metadata."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_dependencies.py'
spec = importlib.util.spec_from_file_location('check_dependencies', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dependency tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def run_main(self, distributions=()):
        output = io.StringIO()
        with patch.object(checker.Path, 'cwd', return_value=self.root), patch.object(
            checker.importlib.metadata, 'distributions', return_value=distributions
        ), contextlib.redirect_stdout(output):
            status = checker.main()
        return status, output.getvalue()

    def requirements(self, text):
        found = {}
        checker.read_requirements(self.write('requirements.txt', text), found, set())
        return found

    def pyproject(self, text):
        found = {}
        checker.read_pyproject(self.write('pyproject.toml', text), found)
        return found

    def test_distribution_normalization_and_unchecked_versions(self):
        class Distribution:
            metadata = {'Name': 'FOO---BAR'}
            version = '1.0'
        self.write('requirements.txt', 'Foo.Bar>=999\nfoo_bar[extra]\n')
        status, output = self.run_main([Distribution()])
        self.assertEqual(status, 0)
        self.assertEqual(output.count('INSTALLED'), 1)
        self.assertIn('Foo.Bar==1.0', output)

    def test_supported_requirement_subset(self):
        for entry in ['one', 'one[extra,two]>=1,<2', 'one (>=1, <2)',
                      'one @ https://example.invalid/one.whl#sha256=abc']:
            with self.subTest(entry=entry):
                self.assertIn('one', self.requirements(entry))

    def test_unsupported_requirements(self):
        for entry in ['one garbage', 'one[', 'one @', 'one @ garbage', 'one-', 'one-1.tar.gz',
                      './local', '-e .', 'https://example.invalid/one.whl',
                      'one; sys_platform == "win32"', '--no-index-junk']:
            with self.subTest(entry=entry):
                self.write('requirements.txt', entry)
                status, output = self.run_main()
                self.assertEqual(status, 2)
                self.assertIn('requirements.txt:1', output)

    def test_include_option_forms(self):
        self.write('child.txt', 'one\n')
        for entry in ['-r child.txt', '-rchild.txt', '-r\tchild.txt',
                      '--requirement child.txt', '--requirement=child.txt']:
            with self.subTest(entry=entry):
                self.assertEqual(set(self.requirements(entry)), {'one'})

    def test_nested_relative_includes_spaces_and_cycles(self):
        self.write('sub dir/a.txt', '-r ../b.txt\nOne\n')
        self.write('b.txt', '-r requirements.txt\nTwo\n')
        found = self.requirements('-r "sub dir/a.txt"\n-r b.txt\n')
        self.assertEqual(set(found), {'one', 'two'})
        self.assertEqual(len(found['two'][1]), 1)

    def test_missing_and_remote_includes(self):
        for entry in ['-r absent.txt', '--requirement=https://example.invalid/r.txt']:
            self.write('requirements.txt', entry)
            self.assertEqual(self.run_main()[0], 2)

    def test_ignored_constraints_and_index_options(self):
        found = self.requirements('-cabsent.txt\n--constraint=absent.txt\n'
                                  '--index-url=https://example.invalid\n'
                                  '--extra-index-url https://example.invalid\n'
                                  '--trusted-host example.invalid\n'
                                  '--find-links=./wheels\n--no-index\none\n')
        self.assertEqual(set(found), {'one'})

    def test_continuations_hashes_bom_crlf_and_comments(self):
        found = self.requirements('\ufeff# heading\r\none==1 \\\r\n'
                                  ' --hash=sha256:abcdef \\\r\n'
                                  ' --hash sha256:123456\t# comment\r\n')
        self.assertEqual(set(found), {'one'})
        self.assertTrue(found['one'][1][0].endswith('requirements.txt:2'))
        self.write('requirements.txt', 'one \\')
        self.assertEqual(self.run_main()[0], 2)

    @unittest.skipIf(checker.tomllib is None, 'Python 3.11+ TOML parser required')
    def test_project_extras_groups_and_poetry(self):
        found = self.pyproject('[project]\ndependencies=["one"]\n'
            '[project.optional-dependencies]\ntest=["two"]\n'
            '[dependency-groups]\nDev_Test=["three"]\nci=[{include-group="dev-test"}]\n'
            '[tool.poetry.dependencies]\npython="^3.11"\nfour="*"\n'
            '[tool.poetry.group.main.dependencies]\nfive="*"\n')
        self.assertEqual(set(found), {'one', 'two', 'three', 'four', 'five'})

    @unittest.skipIf(checker.tomllib is None, 'Python 3.11+ TOML parser required')
    def test_invalid_toml_shapes(self):
        for text in ['[project]\ndependencies="one"', '[project]\ndependencies=[42]',
                     'project=[]', '[project]\noptional-dependencies=[]',
                     '[dependency-groups]\na="one"',
                     '[dependency-groups]\na=[{include-group=42}]',
                     '[tool]\npoetry=[]', '[tool.poetry]\ndependencies=[]',
                     '[project]\ndynamic=["dependencies"]', '[project]\ndynamic=[42]']:
            with self.subTest(text=text):
                self.write('pyproject.toml', text)
                self.assertEqual(self.run_main()[0], 2)

    @unittest.skipIf(checker.tomllib is None, 'Python 3.11+ TOML parser required')
    def test_group_collisions_unknowns_and_cycles(self):
        for text in ['a=[{include-group="b"}]',
                     'a=[{include-group="b"}]\nb=[{include-group="a"}]',
                     'Dev_Test=[]\ndev-test=[]', 'a=[{unknown="b"}]']:
            with self.subTest(text=text):
                self.write('pyproject.toml', '[dependency-groups]\n' + text)
                self.assertEqual(self.run_main()[0], 2)

    def test_python_without_tomllib(self):
        with patch.object(checker, 'tomllib', None):
            self.write('requirements.txt', '')
            self.assertEqual(self.run_main()[0], 0)
            self.write('package.json', '{"dependencies":{}}')
            self.assertEqual(self.run_main()[0], 0)
            self.write('pyproject.toml', '')
            status, output = self.run_main()
            self.assertEqual(status, 2)
            self.assertIn('Python 3.11', output)

    def test_node_sections_optional_peers_and_duplicates(self):
        path = self.write('package.json', json.dumps({
            'dependencies': {'one': '*', '@scope/two': '*'},
            'devDependencies': {'one': '*'}, 'optionalDependencies': {'three': '*'},
            'peerDependencies': {'four': '*', 'five': '*'},
            'peerDependenciesMeta': {'five': {'optional': True}}
        }))
        found = checker.read_package_json(path)
        self.assertEqual(set(found), {'one', '@scope/two', 'three', 'four'})
        self.assertEqual(found['one'], ['dependencies', 'devDependencies'])

    def test_invalid_json_shapes(self):
        for data in [[], {'dependencies': []}, {'dependencies': None},
                     {'dependencies': {'one': 42}}, {'peerDependenciesMeta': []},
                     {'peerDependenciesMeta': {'one': None}},
                     {'peerDependenciesMeta': {'one': {'optional': 'false'}}}]:
            with self.subTest(data=data):
                self.write('package.json', json.dumps(data))
                self.assertEqual(self.run_main()[0], 2)

    def test_node_traversal_rejected(self):
        (self.root / 'node_modules').mkdir()
        for name in ['.', '..', '@scope/..', '@../one', '../one', 'a/b', 'a\\b']:
            with self.subTest(name=name):
                self.write('package.json', json.dumps({'dependencies': {name: '*'}}))
                self.assertEqual(self.run_main()[0], 2)

    def test_node_local_parent_scoped_and_nearest_lookup(self):
        child = self.root / 'project'
        child.mkdir()
        parent = self.write('node_modules/@scope/one/package.json', '{}')
        self.assertEqual(checker.installed_node_package(child, '@scope/one'), parent)
        local = self.write('project/node_modules/@scope/one/package.json', '{}')
        self.assertEqual(checker.installed_node_package(child, '@scope/one'), local)
        self.assertIsNone(checker.installed_node_package(child, 'missing'))

    def test_node_symlink_lookup(self):
        target = self.root / 'target'
        target.mkdir()
        self.write('target/package.json', '{}')
        modules = self.root / 'node_modules'
        modules.mkdir()
        try:
            (modules / 'one').symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Directory symlinks unavailable')
        self.assertIsNotNone(checker.installed_node_package(self.root, 'one'))

    def test_exit_codes_empty_missing_and_no_manifest(self):
        self.assertEqual(self.run_main()[0], 2)
        self.write('requirements.txt', '')
        self.assertEqual(self.run_main()[0], 0)
        self.write('requirement.txt', 'missing-package\n')
        self.assertEqual(self.run_main()[0], 1)

    def test_roots_share_include_tracking(self):
        self.write('requirements.txt', '-r requirement.txt\n')
        self.write('requirement.txt', 'one\n')
        status, output = self.run_main()
        self.assertEqual(status, 1)
        self.assertEqual(output.count('requirement.txt:1'), 1)

    def test_malformed_manifest_encoding_and_syntax(self):
        for name, text in [('package.json', '{'), ('pyproject.toml', '[bad')]:
            self.write(name, text)
            self.assertEqual(self.run_main()[0], 2)
            (self.root / name).unlink()
        (self.root / 'requirements.txt').write_bytes(b'\xff')
        self.assertEqual(self.run_main()[0], 2)

    def test_cli_from_directory_with_spaces(self):
        self.write('package.json', '{}')
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(result.stderr)


if __name__ == '__main__':
    unittest.main()
