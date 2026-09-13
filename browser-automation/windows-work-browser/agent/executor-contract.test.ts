import { selectExecutor } from './executor-contract';
import { AutomationAction } from './action-contract';

const action: AutomationAction = {
  id: 'test-1',
  capability: 'browser.read',
  risk: 'read',
  args: {},
  requiresApproval: false,
  reason: 'read test page',
};

const executor = {
  kind: 'playwright' as const,
  supports: (candidate: AutomationAction) => candidate.capability === 'browser.read',
  execute: async () => ({ actionId: 'test-1', ok: true }),
};

if (selectExecutor([executor], action).kind !== 'playwright') {
  throw new Error('Capability executor selection failed.');
}
