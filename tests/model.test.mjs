import test from 'node:test';
import assert from 'node:assert/strict';
import {matches} from '../web/model.mjs';

const record = {search: 'The commission’s report, Genève and court records', kind:'Public inquiry', region:'Canada'};
test('query words can occur in different parts of a record, regardless of diacritics', () => {
  assert.equal(matches(record, {query:"GENEVE commission's"}), true);
  assert.equal(matches(record, {query:'genève unknown'}), false);
});
test('region and source type narrow a matching query together', () => {
  assert.equal(matches(record, {query:'court', region:'Canada', kind:'Public inquiry'}), true);
  assert.equal(matches(record, {region:'International'}), false);
  assert.equal(matches(record, {kind:'Court record'}), false);
  assert.equal(matches(record, {}), true);
});
