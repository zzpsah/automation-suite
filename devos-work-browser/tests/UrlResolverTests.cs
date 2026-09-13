using Devos.WorkBrowser.Browser;

namespace Devos.WorkBrowser.Tests;

public sealed class UrlResolverTests
{
    [Theory]
    [InlineData("https://example.com/path", "https://example.com/path")]
    [InlineData("example.com", "https://example.com/")]
    public void Resolve_RecognizesUrls(string input, string expected)
    {
        Assert.Equal(expected, UrlResolver.Resolve(input).ToString());
    }

    [Fact]
    public void Resolve_UsesSearchForNaturalLanguage()
    {
        var uri = UrlResolver.Resolve("student portal बिहार");
        Assert.StartsWith("https://www.google.com/search?q=", uri.ToString());
        Assert.Contains("student", uri.ToString());
    }

    [Fact]
    public void Resolve_UsesHomeForBlankInput()
    {
        Assert.Equal("https://www.google.com/", UrlResolver.Resolve("   ").ToString());
    }
}
