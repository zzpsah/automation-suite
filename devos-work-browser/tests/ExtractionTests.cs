using Devos.WorkBrowser.Extraction;
using Xunit;

namespace Devos.WorkBrowser.Tests;

public sealed class ExtractionTests
{
    [Fact]
    public void Parse_AndCsv_PreserveRows()
    {
        var rows = TableExtraction.Parse("[[\"Name\",\"Status\"],[\"Asha\",\"Done\"],[\"Ravi\",\"Needs, review\"]]");
        Assert.Equal(3, rows.Count);
        Assert.Equal("Asha", rows[1][0]);
        var csv = TableExtraction.ToCsv(rows);
        Assert.Contains("\"Needs, review\"", csv);
    }
}
