using Devos.WorkBrowser.Browser;
using Xunit;

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

    [Theory]
    [InlineData("eshikshakosh", "https://eshikshakosh.bihar.gov.in/")]
    [InlineData("e shiksha kosh", "https://eshikshakosh.bihar.gov.in/")]
    [InlineData("example.com", "https://example.com/")]
    [InlineData("https://example.com/path", "https://example.com/path")]
    public void CommandNavigationResolver_UsesDirectNavigation(string input, string expected)
    {
        Assert.Equal(expected, CommandNavigationResolver.Resolve(input).ToString());
    }

    [Fact]
    public void CommandNavigationResolver_DoesNotSilentlySearchUnknownNames()
    {
        var error = Assert.Throws<InvalidOperationException>(() => CommandNavigationResolver.Resolve("some unknown portal"));
        Assert.Contains("Unknown direct site name", error.Message);
    }
}
