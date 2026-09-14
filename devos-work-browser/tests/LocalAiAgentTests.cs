using System.Net;
using System.Net.Http;
using System.Text;
using Devos.WorkBrowser.Agent;
using Devos.WorkBrowser.Runtime;
using Xunit;

namespace Devos.WorkBrowser.Tests;

public sealed class LocalAiAgentTests
{
    [Fact]
    public void ParseDecision_MapsSingleStructuredBrowserAction()
    {
        var decision = LocalAiAgent.ParseDecision("""
            {"done":false,"message":"Open the portal","description":"navigate to portal","action":{"kind":"Navigate","target":"https://example.com/","value":null}}
            """);

        Assert.False(decision.Done);
        Assert.NotNull(decision.Action);
        Assert.Equal(BrowserActionKind.Navigate, decision.Action!.Kind);
        Assert.Equal("https://example.com/", decision.Action.Target);
    }

    [Fact]
    public void ParseDecision_AllowsDoneWithoutAction()
    {
        var decision = LocalAiAgent.ParseDecision("""
            {"done":true,"message":"Finished","description":"","action":null}
            """);

        Assert.True(decision.Done);
        Assert.Null(decision.Action);
        Assert.Equal("Finished", decision.Message);
    }

    [Theory]
    [InlineData("submit the application", "tag=button type=submit text=Submit")]
    [InlineData("save the record", "tag=button text=Save")]
    [InlineData("delete selected row", "tag=button text=Delete")]
    public void SafetyPolicy_RequiresApprovalForCommittingUi(string description, string descriptor)
    {
        var action = new BrowserAction(BrowserActionKind.Click, "[data-devos-ref=\"d4\"]");
        Assert.True(AgentSafetyPolicy.RequiresApproval(action, description, descriptor));
    }

    [Fact]
    public void SafetyPolicy_DoesNotRequireApprovalForNormalNavigation()
    {
        var action = new BrowserAction(BrowserActionKind.Navigate, "example.com");
        Assert.False(AgentSafetyPolicy.RequiresApproval(action, "open example", null));
    }

    [Theory]
    [InlineData("enter OTP")]
    [InlineData("solve CAPTCHA")]
    [InlineData("type verification code")]
    public void SafetyPolicy_StopsHumanVerificationSteps(string description)
    {
        Assert.True(AgentSafetyPolicy.RequiresHumanInteraction(description, null));
    }

    [Fact]
    public async Task LocalAgent_UsesOllamaCompatibleJsonChatContract()
    {
        var previousDisableValue = Environment.GetEnvironmentVariable("DEVOS_DISABLE_LOCAL_AI");
        try
        {
            // The GitHub workflow deliberately disables runner-local AI so normal
            // packaged tests never depend on Ollama. This unit test uses a fake
            // localhost-compatible transport, so isolate it from that process flag.
            Environment.SetEnvironmentVariable("DEVOS_DISABLE_LOCAL_AI", null);

            var handler = new StubHandler(request =>
            {
                if (request.RequestUri!.AbsolutePath.EndsWith("/api/tags", StringComparison.Ordinal))
                {
                    return Json(HttpStatusCode.OK, "{\"models\":[{\"name\":\"qwen3:4b\"}]}");
                }

                if (request.RequestUri.AbsolutePath.EndsWith("/api/chat", StringComparison.Ordinal))
                {
                    return Json(HttpStatusCode.OK,
                        "{\"message\":{\"content\":\"{\\\"done\\\":false,\\\"message\\\":\\\"Click next\\\",\\\"description\\\":\\\"click next page\\\",\\\"action\\\":{\\\"kind\\\":\\\"Click\\\",\\\"target\\\":\\\"#next\\\",\\\"value\\\":null}}\"}}");
                }

                return Json(HttpStatusCode.NotFound, "{}");
            });
            var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:11434/") };
            var agent = new LocalAiAgent(http, "qwen3:4b");

            Assert.True(await agent.IsAvailableAsync());
            var decision = await agent.GetNextStepAsync("go next", "{\"elements\":[]}", null);

            Assert.False(decision.Done);
            Assert.Equal(BrowserActionKind.Click, decision.Action!.Kind);
            Assert.Equal("#next", decision.Action.Target);
        }
        finally
        {
            Environment.SetEnvironmentVariable("DEVOS_DISABLE_LOCAL_AI", previousDisableValue);
        }
    }

    private static HttpResponseMessage Json(HttpStatusCode code, string json)
        => new(code) { Content = new StringContent(json, Encoding.UTF8, "application/json") };

    private sealed class StubHandler : HttpMessageHandler
    {
        private readonly Func<HttpRequestMessage, HttpResponseMessage> _handler;

        public StubHandler(Func<HttpRequestMessage, HttpResponseMessage> handler) => _handler = handler;

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
            => Task.FromResult(_handler(request));
    }
}
