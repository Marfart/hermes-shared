const assert = require('node:assert/strict');
const path = require('node:path');

const repo = 'C:/Users/Admin/Desktop/Working/GitHub_Overnight_Study/node-red';
const flowUtil = require(path.join(repo, 'packages/node_modules/@node-red/runtime/lib/flows/util.js'));

const cases = [
  {
    name: 'editor position is not a runtime change',
    oldNode: { id: 'sensor', type: 'inject', x: 20, y: 30, wires: [] },
    newNode: { id: 'sensor', type: 'inject', x: 500, y: 900, wires: [] },
    expected: false,
  },
  {
    name: 'wire topology is classified separately from node properties',
    oldNode: { id: 'sensor', type: 'inject', x: 20, y: 30, wires: [['old-target']] },
    newNode: { id: 'sensor', type: 'inject', x: 20, y: 30, wires: [['new-target']] },
    expected: false,
  },
  {
    name: 'device/runtime property change requires redeploy',
    oldNode: { id: 'sensor', type: 'modbus-read', x: 20, y: 30, wires: [], unitId: 1 },
    newNode: { id: 'sensor', type: 'modbus-read', x: 20, y: 30, wires: [], unitId: 2 },
    expected: true,
  },
];

for (const test of cases) {
  assert.equal(flowUtil.diffNodes(test.oldNode, test.newNode), test.expected, test.name);
  process.stdout.write(`PASS ${test.name}\n`);
}
process.stdout.write(`All ${cases.length} original probes passed.\n`);
