"""Owned finite CLI fixtures, not new scientific baseline measurements."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class KernelCliInputs(unittest.TestCase):
    def invoke(self,cases,output):
        return subprocess.run([sys.executable,'-B',str(ROOT/'src/kernel_baseline.py'),
            '--cases',str(cases),'--output',str(output)],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',timeout=15)

    def rejected(self,kind):
        with tempfile.TemporaryDirectory(prefix='kernel-input-') as directory:
            base=Path(directory);cases=base/'cases'
            if kind=='file':cases.write_text('not a directory',encoding='utf-8')
            if kind in ('empty','nonjson'):
                cases.mkdir()
                if kind=='nonjson':(cases/'note.txt').write_text('not an input case',encoding='utf-8')
            output=base/'new-output/unchanged.json'
            r=self.invoke(cases,output)
            self.assertNotEqual(r.returncode,0,r.stdout)
            self.assertFalse(output.parent.exists(),'Invalid input must not create result directories')
            self.assertIn('cases',r.stderr.casefold())

    def test_missing_directory_is_not_empty_success(self):self.rejected('missing')
    def test_file_is_not_a_case_directory(self):self.rejected('file')
    def test_empty_directory_is_not_a_baseline(self):self.rejected('empty')
    def test_unrelated_files_are_not_a_corpus(self):self.rejected('nonjson')

    def test_existing_output_survives_invalid_input(self):
        with tempfile.TemporaryDirectory(prefix='kernel-input-') as directory:
            base=Path(directory);output=base/'existing.json';original=b'owned old output\n'
            output.write_bytes(original)
            r=self.invoke(base/'absent',output)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(output.read_bytes(),original)

    def test_one_valid_zero_obligation_case_is_supported(self):
        with tempfile.TemporaryDirectory(prefix='kernel-input-') as directory:
            base=Path(directory);cases=base/'cases';cases.mkdir()
            case=dict(id='owned-zero',family='owned-control',requests=[[0]],
                      policies=[dict(combiner='DO',rules=[])],mutations=[],profile='declared')
            (cases/'one.json').write_text(json.dumps(case),encoding='utf-8')
            output=base/'output.json';r=self.invoke(cases,output)
            self.assertEqual(r.returncode,0,r.stderr)
            rows=json.loads(output.read_text(encoding='utf-8'))['cases']
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['suite'],[])
            self.assertEqual(rows[0]['detectable'],0)
            self.assertEqual(rows[0]['killed'],0)


if __name__=='__main__':unittest.main()
