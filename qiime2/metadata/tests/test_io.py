# ----------------------------------------------------------------------------
# Copyright (c) 2016-2018, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import collections
import os.path
import pkg_resources
import tempfile
import unittest

import numpy as np
import pandas as pd

from qiime2.metadata import Metadata, MetadataFileError


def get_data_path(filename):
    return pkg_resources.resource_filename('qiime2.metadata.tests',
                                           'data/%s' % filename)

# NOTE: many of the test files in the `data` directory intentionally have
# leading/trailing whitespace characters on some lines, as well as mixed usage
# of spaces, tabs, carriage returns, and newlines. When editing these files,
# please make sure your code editor doesn't strip these leading/trailing
# whitespace characters (e.g. Atom does this by default), nor automatically
# modify the files in some other way such as converting Windows-style CRLF
# line terminators to Unix-style newlines.
#
# When committing changes to the files, carefully review the diff to make sure
# unintended changes weren't introduced.


class TestLoadErrors(unittest.TestCase):
    def test_path_does_not_exist(self):
        with self.assertRaisesRegex(MetadataFileError,
                                    "Metadata file path doesn't exist"):
            Metadata.load(
                '/qiime2/unit/tests/hopefully/this/path/does/not/exist')

    def test_path_is_directory(self):
        fp = get_data_path('valid')

        with self.assertRaisesRegex(MetadataFileError,
                                    "path points to something other than a "
                                    "file"):
            Metadata.load(fp)

    def test_non_utf_8_file(self):
        fp = get_data_path('invalid/non-utf-8.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'encoded as UTF-8 or ASCII'):
            Metadata.load(fp)

    def test_empty_file(self):
        fp = get_data_path('invalid/empty-file')

        with self.assertRaisesRegex(MetadataFileError,
                                    'locate header.*file may be empty'):
            Metadata.load(fp)

    def test_comments_and_empty_rows_only(self):
        fp = get_data_path('invalid/comments-and-empty-rows-only.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'locate header.*only of comments or empty '
                                    'rows'):
            Metadata.load(fp)

    def test_header_only(self):
        fp = get_data_path('invalid/header-only.tsv')

        with self.assertRaisesRegex(MetadataFileError, 'at least one ID'):
            Metadata.load(fp)

    def test_header_only_with_comments_and_empty_rows(self):
        fp = get_data_path(
            'invalid/header-only-with-comments-and-empty-rows.tsv')

        with self.assertRaisesRegex(MetadataFileError, 'at least one ID'):
            Metadata.load(fp)

    def test_qiime1_empty_mapping_file(self):
        fp = get_data_path('invalid/qiime1-empty.tsv')

        with self.assertRaisesRegex(MetadataFileError, 'at least one ID'):
            Metadata.load(fp)

    def test_invalid_header(self):
        fp = get_data_path('invalid/invalid-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'unrecognized ID column name.*'
                                    'invalid_id_header'):
            Metadata.load(fp)

    def test_empty_id(self):
        fp = get_data_path('invalid/empty-id.tsv')

        with self.assertRaisesRegex(MetadataFileError, 'empty metadata ID'):
            Metadata.load(fp)

    def test_whitespace_only_id(self):
        fp = get_data_path('invalid/whitespace-only-id.tsv')

        with self.assertRaisesRegex(MetadataFileError, 'empty metadata ID'):
            Metadata.load(fp)

    def test_empty_column_name(self):
        fp = get_data_path('invalid/empty-column-name.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'column without a name'):
            Metadata.load(fp)

    def test_whitespace_only_column_name(self):
        fp = get_data_path('invalid/whitespace-only-column-name.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'column without a name'):
            Metadata.load(fp)

    def test_duplicate_ids(self):
        fp = get_data_path('invalid/duplicate-ids.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'IDs must be unique.*id1'):
            Metadata.load(fp)

    def test_duplicate_ids_with_whitespace(self):
        fp = get_data_path('invalid/duplicate-ids-with-whitespace.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'IDs must be unique.*id1'):
            Metadata.load(fp)

    def test_duplicate_column_names(self):
        fp = get_data_path('invalid/duplicate-column-names.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'Column names must be unique.*col1'):
            Metadata.load(fp)

    def test_duplicate_column_names_with_whitespace(self):
        fp = get_data_path(
            'invalid/duplicate-column-names-with-whitespace.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'Column names must be unique.*col1'):
            Metadata.load(fp)

    def test_id_conflicts_with_id_header(self):
        fp = get_data_path('invalid/id-conflicts-with-id-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    "ID 'id' conflicts.*ID column header"):
            Metadata.load(fp)

    def test_column_name_conflicts_with_id_header(self):
        fp = get_data_path(
            'invalid/column-name-conflicts-with-id-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    "column name 'featureid' conflicts.*ID "
                                    "column header"):
            Metadata.load(fp)

    def test_column_types_unrecognized_column_name(self):
        fp = get_data_path('valid/simple.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'not_a_column.*column_types.*not a column '
                                    'in the metadata file'):
            Metadata.load(fp, column_types={'not_a_column': 'numeric'})

    def test_column_types_unrecognized_column_type(self):
        fp = get_data_path('valid/simple.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'col2.*column_types.*unrecognized column '
                                    'type.*CATEGORICAL'):
            Metadata.load(fp, column_types={'col1': 'numeric',
                                            'col2': 'CATEGORICAL'})

    def test_column_types_not_convertible_to_numeric(self):
        fp = get_data_path('valid/simple.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    "column 'col3' to numeric.*could not be "
                                    "interpreted as numeric: 'bar', 'foo'"):
            Metadata.load(fp, column_types={'col1': 'numeric',
                                            'col2': 'categorical',
                                            'col3': 'numeric'})

    def test_column_types_override_directive_not_convertible_to_numeric(self):
        fp = get_data_path('valid/simple-with-directive.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    "column 'col3' to numeric.*could not be "
                                    "interpreted as numeric: 'bar', 'foo'"):
            Metadata.load(fp, column_types={'col3': 'numeric'})

    def test_directive_before_header(self):
        fp = get_data_path('invalid/directive-before-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'directive.*#q2:types.*searching for '
                                    'header'):
            Metadata.load(fp)

    def test_unrecognized_directive(self):
        fp = get_data_path('invalid/unrecognized-directive.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'Unrecognized directive.*#q2:foo.*'
                                    '#q2:types directive is supported'):
            Metadata.load(fp)

    def test_duplicate_directives(self):
        fp = get_data_path('invalid/duplicate-directives.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'duplicate directive.*#q2:types'):
            Metadata.load(fp)

    def test_unrecognized_column_type_in_directive(self):
        fp = get_data_path('invalid/unrecognized-column-type.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'col2.*unrecognized column type.*foo.*'
                                    '#q2:types directive'):
            Metadata.load(fp)

    def test_column_types_directive_not_convertible_to_numeric(self):
        fp = get_data_path('invalid/types-directive-non-numeric.tsv')

        # This error message regex is intentionally verbose because we want to
        # assert that many different types of non-numeric strings aren't
        # interpreted as numbers. The error message displays a sorted list of
        # all values that couldn't be converted to numbers, making it possible
        # to test a variety of non-numeric strings in a single test case.
        msg = (r"column 'col2' to numeric.*could not be interpreted as "
               "numeric: '\$42', '\+inf', '-inf', '0xAF', '1,000', "
               "'1\.000\.0', '1_000_000', '1e3e4', 'Infinity', 'NA', 'NaN', "
               "'a', 'e3', 'foo', 'inf', 'nan', 'sample-1'")
        with self.assertRaisesRegex(MetadataFileError, msg):
            Metadata.load(fp)

    def test_directive_after_directives_section(self):
        fp = get_data_path(
            'invalid/directive-after-directives-section.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    '#q2:types.*outside of the directives '
                                    'section'):
            Metadata.load(fp)

    def test_directive_longer_than_header(self):
        fp = get_data_path('invalid/directive-longer-than-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'row has 5 cells.*header declares 4 '
                                    'cells'):
            Metadata.load(fp)

    def test_data_longer_than_header(self):
        fp = get_data_path('invalid/data-longer-than-header.tsv')

        with self.assertRaisesRegex(MetadataFileError,
                                    'row has 5 cells.*header declares 4 '
                                    'cells'):
            Metadata.load(fp)


class TestLoadSuccess(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory(
            prefix='qiime2-metadata-tests-temp-')
        self.temp_dir = self.temp_dir_obj.name

        # This Metadata object is compared against observed Metadata objects in
        # many of the tests, so just define it once here.
        self.simple_md = Metadata(
            pd.DataFrame({'col1': [1.0, 2.0, 3.0],
                          'col2': ['a', 'b', 'c'],
                          'col3': ['foo', 'bar', '42']},
                         index=pd.Index(['id1', 'id2', 'id3'], name='id')))

        # Basic sanity check to make sure the columns are ordered and typed as
        # expected. It'd be unfortunate to compare observed results to expected
        # results that aren't representing what we think they are!
        obs_columns = [(name, props.type)
                       for name, props in self.simple_md.columns.items()]
        exp_columns = [('col1', 'numeric'), ('col2', 'categorical'),
                       ('col3', 'categorical')]
        self.assertEqual(obs_columns, exp_columns)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_simple(self):
        # Simple metadata file without comments, empty rows, jaggedness,
        # missing data, odd IDs or column names, directives, etc. The file has
        # multiple column types (numeric, categorical, and something that has
        # mixed numbers and strings, which must be interpreted as categorical).
        fp = get_data_path('valid/simple.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_different_file_extension(self):
        fp = get_data_path('valid/simple.txt')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_no_newline_at_eof(self):
        fp = get_data_path('valid/no-newline-at-eof.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_unix_line_endings(self):
        fp = get_data_path('valid/unix-line-endings.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_windows_line_endings(self):
        fp = get_data_path('valid/windows-line-endings.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_mac_line_endings(self):
        fp = get_data_path('valid/mac-line-endings.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_no_source_artifacts(self):
        fp = get_data_path('valid/simple.tsv')

        metadata = Metadata.load(fp)

        self.assertEqual(metadata.artifacts, ())

    def test_retains_column_order(self):
        # Explicitly test that the file's column order is retained in the
        # Metadata object. Many of the test cases use files with column names
        # in alphabetical order (e.g. "col1", "col2", "col3"), which matches
        # how pandas orders columns in a DataFrame when supplied with a dict
        # (many of the test cases use this feature of the DataFrame
        # constructor when constructing the expected DataFrame).
        fp = get_data_path('valid/column-order.tsv')

        obs_md = Metadata.load(fp)

        # Supply DataFrame constructor with explicit column ordering instead of
        # a dict.
        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_columns = ['z', 'y', 'x']
        exp_data = [
            [1.0, 'a', 'foo'],
            [2.0, 'b', 'bar'],
            [3.0, 'c', '42']
        ]
        exp_df = pd.DataFrame(exp_data, index=exp_index, columns=exp_columns)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_leading_trailing_whitespace(self):
        fp = get_data_path('valid/leading-trailing-whitespace.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_comments(self):
        fp = get_data_path('valid/comments.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_empty_rows(self):
        fp = get_data_path('valid/empty-rows.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_qiime1_mapping_file(self):
        fp = get_data_path('valid/qiime1.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='#SampleID')
        exp_df = pd.DataFrame({'col1': [1.0, 2.0, 3.0],
                               'col2': ['a', 'b', 'c'],
                               'col3': ['foo', 'bar', '42']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_qiita_sample_information_file(self):
        fp = get_data_path('valid/qiita-sample-information.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id.1', 'id.2'], name='sample_name')
        exp_df = pd.DataFrame({
            'DESCRIPTION': ['description 1', 'description 2'],
            'TITLE': ['A Title', 'Another Title']},
            index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_qiita_preparation_information_file(self):
        fp = get_data_path('valid/qiita-preparation-information.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id.1', 'id.2'], name='sample_name')
        exp_df = pd.DataFrame({
            'BARCODE': ['ACGT', 'TGCA'],
            'EXPERIMENT_DESIGN_DESCRIPTION': ['longitudinal study',
                                              'longitudinal study']},
            index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_biom_observation_metadata_file(self):
        fp = get_data_path('valid/biom-observation-metadata.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['OTU_1', 'OTU_2'], name='#OTUID')
        exp_df = pd.DataFrame([['k__Bacteria;p__Firmicutes', 0.890],
                               ['k__Bacteria', 0.9999]],
                              columns=['taxonomy', 'confidence'],
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_supported_id_headers(self):
        case_insensitive = {
            'id', 'sampleid', 'sample id', 'sample-id', 'featureid',
            'feature id', 'feature-id'
        }

        exact_match = {
            '#SampleID', '#Sample ID', '#OTUID', '#OTU ID', 'sample_name'
        }

        # Build a set of supported headers, including exact matches and headers
        # with different casing.
        headers = set()
        for header in case_insensitive:
            headers.add(header)
            headers.add(header.upper())
            headers.add(header.title())
        for header in exact_match:
            headers.add(header)

        fp = os.path.join(self.temp_dir, 'metadata.tsv')
        count = 0
        for header in headers:
            with open(fp, 'w') as fh:
                fh.write('%s\tcolumn\nid1\tfoo\nid2\tbar\n' % header)

            obs_md = Metadata.load(fp)

            exp_index = pd.Index(['id1', 'id2'], name=header)
            exp_df = pd.DataFrame({'column': ['foo', 'bar']}, index=exp_index)
            exp_md = Metadata(exp_df)

            self.assertEqual(obs_md, exp_md)
            count += 1

        # Since this test case is a little complicated, make sure that the
        # expected number of comparisons are happening.
        self.assertEqual(count, 26)

    def test_recommended_ids(self):
        fp = get_data_path('valid/recommended-ids.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['c6ca034a-223f-40b4-a0e0-45942912a5ea', 'My.ID'],
                             name='id')
        exp_df = pd.DataFrame({'col1': ['foo', 'bar']}, index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_non_standard_characters(self):
        # Test that non-standard characters in IDs, column names, and cells are
        # handled correctly. The test case isn't exhaustive (e.g. it doesn't
        # test every Unicode character; that would be a nice additional test
        # case to have in the future). Instead, this test aims to be more of an
        # integration test for the robustness of the reader to non-standard
        # data. Many of the characters and their placement within the data file
        # are based on use-cases/bugs reported on the forum, Slack, etc. The
        # data file has comments explaining these test case choices in more
        # detail.
        fp = get_data_path('valid/non-standard-characters.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['©id##1', '((id))2', "'id_3<>'", '"id#4"',
                              'i d\r\t\n5'], name='id')
        exp_columns = ['↩c@l1™', 'col(#2)', "#col'3", '"<col_4>"',
                       'col\t  \r\n5']
        exp_data = [
            ['ƒoo', '(foo)', '#f o #o', 'fo\ro', np.nan],
            ["''2''", 'b#r', 'ba\nr', np.nan, np.nan],
            ['b"ar', 'c\td', '4\r\n2', np.nan, np.nan],
            ['b__a_z', '<42>', '>42', np.nan, np.nan],
            ['baz', np.nan, '42']
        ]
        exp_df = pd.DataFrame(exp_data, index=exp_index, columns=exp_columns)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_missing_data(self):
        fp = get_data_path('valid/missing-data.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['None', 'nan', 'NA'], name='id')
        exp_df = pd.DataFrame(collections.OrderedDict([
            ('col1', [1.0, np.nan, np.nan]),
            ('NA', [np.nan, np.nan, np.nan]),
            ('col3', ['null', 'N/A', 'NA']),
            ('col4', np.array([np.nan, np.nan, np.nan], dtype=object))]),
            index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

        # Test that column types are correct (mainly for the two empty columns;
        # one should be numeric, the other categorical).
        obs_columns = [(name, props.type)
                       for name, props in obs_md.columns.items()]
        exp_columns = [('col1', 'numeric'), ('NA', 'numeric'),
                       ('col3', 'categorical'), ('col4', 'categorical')]
        self.assertEqual(obs_columns, exp_columns)

    def test_minimal_file(self):
        # Simplest possible metadata file consists of one ID and zero columns.
        fp = get_data_path('valid/minimal.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['a'], name='id')
        exp_df = pd.DataFrame({}, index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_single_id(self):
        fp = get_data_path('valid/single-id.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1'], name='id')
        exp_df = pd.DataFrame({'col1': [1.0], 'col2': ['a'], 'col3': ['foo']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_no_columns(self):
        fp = get_data_path('valid/no-columns.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['a', 'b', 'my-id'], name='id')
        exp_df = pd.DataFrame({}, index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_single_column(self):
        fp = get_data_path('valid/single-column.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': [1.0, 2.0, 3.0]}, index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_trailing_columns(self):
        fp = get_data_path('valid/trailing-columns.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_jagged_trailing_columns(self):
        # Test case based on https://github.com/qiime2/qiime2/issues/335
        fp = get_data_path('valid/jagged-trailing-columns.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_padding_rows_shorter_than_header(self):
        fp = get_data_path('valid/rows-shorter-than-header.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': [1.0, 2.0, np.nan],
                               'col2': ['a', np.nan, np.nan],
                               'col3': [np.nan, np.nan, np.nan]},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_all_cells_padded(self):
        fp = get_data_path('valid/all-cells-padded.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': [np.nan, np.nan, np.nan],
                               'col2': [np.nan, np.nan, np.nan],
                               'col3': [np.nan, np.nan, np.nan]},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_does_not_cast_ids_or_column_names(self):
        fp = get_data_path('valid/no-id-or-column-name-type-cast.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['0.000001', '0.004000', '0.000000'],
                             dtype=object, name='id')
        exp_columns = ['42.0', '1000', '-4.2']
        exp_data = [
            [2.0, 'b', 2.5],
            [1.0, 'b', 4.2],
            [3.0, 'c', -9.999]
        ]
        exp_df = pd.DataFrame(exp_data, index=exp_index, columns=exp_columns)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_numeric_column(self):
        fp = get_data_path('valid/numeric-column.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3', 'id4', 'id5', 'id6', 'id7',
                              'id8'], name='id')
        exp_df = pd.DataFrame({'col1': [0.0, 2.0, 0.0003, -4.2, 1e-4, 1e4,
                                        1.5e2, np.nan]},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_numeric_column_as_categorical(self):
        fp = get_data_path('valid/numeric-column.tsv')

        obs_md = Metadata.load(fp, column_types={'col1': 'categorical'})

        exp_index = pd.Index(['id1', 'id2', 'id3', 'id4', 'id5', 'id6', 'id7',
                              'id8'], name='id')
        exp_df = pd.DataFrame({'col1': ['0', '2.0', '0.00030', '-4.2', '1e-4',
                                        '1e4', '+1.5E+2', np.nan]},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_with_complete_types_directive(self):
        fp = get_data_path('valid/complete-types-directive.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': ['1', '2', '3'],
                               'col2': ['a', 'b', 'c'],
                               'col3': ['foo', 'bar', '42']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_with_partial_types_directive(self):
        fp = get_data_path('valid/partial-types-directive.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': ['1', '2', '3'],
                               'col2': ['a', 'b', 'c'],
                               'col3': ['foo', 'bar', '42']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_with_empty_types_directive(self):
        fp = get_data_path('valid/empty-types-directive.tsv')

        obs_md = Metadata.load(fp)

        self.assertEqual(obs_md, self.simple_md)

    def test_with_case_insensitive_types_directive(self):
        fp = get_data_path('valid/case-insensitive-types-directive.tsv')

        obs_md = Metadata.load(fp)

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': ['1', '2', '3'],
                               'col2': ['a', 'b', 'c'],
                               'col3': [-5.0, 0.0, 42.0]},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_column_types_without_directive(self):
        fp = get_data_path('valid/simple.tsv')

        obs_md = Metadata.load(fp, column_types={'col1': 'categorical'})

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': ['1', '2', '3'],
                               'col2': ['a', 'b', 'c'],
                               'col3': ['foo', 'bar', '42']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)

    def test_column_types_override_directive(self):
        fp = get_data_path('valid/simple-with-directive.tsv')

        obs_md = Metadata.load(fp, column_types={'col1': 'categorical',
                                                 'col2': 'categorical'})

        exp_index = pd.Index(['id1', 'id2', 'id3'], name='id')
        exp_df = pd.DataFrame({'col1': ['1', '2', '3'],
                               'col2': ['a', 'b', 'c'],
                               'col3': ['foo', 'bar', '42']},
                              index=exp_index)
        exp_md = Metadata(exp_df)

        self.assertEqual(obs_md, exp_md)


if __name__ == '__main__':
    unittest.main()