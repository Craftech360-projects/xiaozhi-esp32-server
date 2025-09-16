// Basic package.json sanity checks (name/version must exist)
const fs = require('fs');
const path = require('path');

describe('package.json', () => {
  test('has name and version', () => {
    const pkgPath = path.join(__dirname, '..', 'package.json');
    const raw = fs.readFileSync(pkgPath, 'utf8');
    const pkg = JSON.parse(raw);
    expect(typeof pkg.name).toBe('string');
    expect(pkg.name.length).toBeGreaterThan(0);
    expect(typeof pkg.version).toBe('string');
    expect(pkg.version.length).toBeGreaterThan(0);
  });
});
