using Devos.WorkBrowser.Planning;
using Devos.WorkBrowser.Runtime;
using Xunit;

namespace Devos.WorkBrowser.Tests;

public sealed class PlanningTests
{
    [Fact]
    public void Planner_MapsReadWithoutApproval()
    {
        var plan = new NaturalLanguagePlanner().Plan("read #status");
        Assert.False(plan.RequiresApproval);
        Assert.Single(plan.Actions);
        Assert.Equal(BrowserActionKind.ReadText, plan.Actions[0].Kind);
    }

    [Fact]
    public void Planner_MapsSubmitWithApproval()
    {
        var plan = new NaturalLanguagePlanner().Plan("submit #save");
        Assert.True(plan.RequiresApproval);
        Assert.Equal(BrowserActionKind.Click, plan.Actions[0].Kind);
    }

    [Fact]
    public void Planner_BuildsBoundedSequenceAndPropagatesApproval()
    {
        var plan = new NaturalLanguagePlanner().Plan("click #next; wait for #students; submit #save");

        Assert.Equal(3, plan.Actions.Count);
        Assert.Equal(BrowserActionKind.Click, plan.Actions[0].Kind);
        Assert.Equal(BrowserActionKind.WaitForSelector, plan.Actions[1].Kind);
        Assert.Equal(BrowserActionKind.Click, plan.Actions[2].Kind);
        Assert.True(plan.RequiresApproval);
    }

    [Theory]
    [InlineData(OperationKind.Upload)]
    [InlineData(OperationKind.Submit)]
    [InlineData(OperationKind.Delete)]
    [InlineData(OperationKind.Send)]
    public void ApprovalPolicy_RequiresApprovalForCommittingOperations(OperationKind operation)
    {
        Assert.True(new ApprovalPolicy().RequiresApproval(operation));
    }
}
