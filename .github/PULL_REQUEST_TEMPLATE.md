# 🛡️ Pull Request

## 📝 Description

**Please include a summary of the changes and the related issue.**

Fixes # (issue number)

## 🎯 Type of Change

Please delete options that are not relevant.

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🎨 Code style update (formatting, renaming)
- [ ] ♻️ Refactoring (no functional changes, no api changes)
- [ ] 🔧 Build configuration change
- [ ] ✅ Test update
- [ ] 🚀 Performance improvement

## 🧪 Testing Checklist

**Please confirm that you have completed the following:**

- [ ] I have run `pytest tests/` locally and all tests pass
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have run `ruff check aegis/` and fixed all linting issues
- [ ] I have run `black aegis/` to format my code
- [ ] I have run `mypy aegis/` and fixed all type errors
- [ ] I have tested on my local environment (OS: **\_\_**)

## 🛡️ Security & Safety

**For changes that touch critical modules (Mapper, Patcher, Git operations):**

- [ ] I have verified that my changes maintain AST parsing accuracy
- [ ] I have verified that my changes don't introduce security vulnerabilities
- [ ] I have verified that Git sandbox isolation is not compromised
- [ ] I have tested with real-world codebases (not just synthetic tests)

## 📚 Documentation

- [ ] I have updated the README.md if needed
- [ ] I have updated docstrings for new/modified functions
- [ ] I have updated CHANGELOG.md
- [ ] I have updated relevant documentation in `docs/`

## 🔄 Backward Compatibility

- [ ] This PR maintains backward compatibility
- [ ] This PR requires a major version bump (breaking changes)
- [ ] I have added migration notes to CHANGELOG.md for breaking changes

## 📸 Screenshots / Examples

**If applicable, add screenshots or example outputs to help explain your changes.**

<details>
<summary>Before</summary>

```
# Paste before output
```

</details>

<details>
<summary>After</summary>

```
# Paste after output
```

</details>

## 🎯 Performance Impact

**For performance-related changes:**

- [ ] I have benchmarked my changes
- [ ] Performance improved by: \_\_\_\_%
- [ ] Memory usage: [ ] Decreased [ ] Increased [ ] No change

## ✅ Pre-Merge Checklist

**Please ensure all items are checked before requesting review:**

- [ ] My code follows the project's coding style (PEP 8, type hints)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have rebased on the latest `main` branch
- [ ] All CI checks are passing

## 💬 Additional Notes

**Any additional information or context for reviewers.**

---

**Thank you for contributing to Aegis Box! 🛡️**

## 📝 Reviewer Notes

_For maintainers only:_

- [ ] Code review completed
- [ ] Tests reviewed
- [ ] Documentation reviewed
- [ ] Ready to merge
