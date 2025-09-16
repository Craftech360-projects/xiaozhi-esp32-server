// Verifies app.js is valid JavaScript by parsing it (no execution)
const fs = require('fs');
const path = require('path');

describe('syntax', () => {
  test('app.js parses without syntax errors', () => {
    const file = path.join(__dirname, '..', 'app.js');
    const src = fs.readFileSync(file, 'utf8');
    expect(() => {
      // new Function throws on syntax errors, but does not execute the code
      // (so it’s safe even if app.js starts servers on require)
      // eslint-disable-next-line no-new-func
      new Function(src);
    }).not.toThrow();
  });
});
