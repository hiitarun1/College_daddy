## Contributing to College Daddy

Thanks for helping improve College Daddy! This guide keeps contributions simple, consistent, and student-focused.

### 1. Philosophy
- Prioritize student impact—every change should make learning easier.
- Keep the app fast, lightweight, and accessible across devices.
- Respect privacy—no personal data without consent.

### 2. Getting Started
1. Fork and clone the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/<name>
   ```
3. Install dependencies and run locally:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
4. Open `index.html` or the relevant page to confirm your setup.

### 3. Code Standards
- **Python**: Follow PEP 8, use clear names and docstrings.
- **JavaScript**: Use ES6+, keep modules organized under `assets/js/`.
- **CSS/HTML**: Stick to existing patterns, stay semantic, and maintain accessibility.
- **Assets**: Compress large files and store them in the correct `assets/` folder.

### 4. Data Contributions
- Add only content that is approved for sharing.
- Place files in the proper `data/notes/semester-x/...` path.
- Include metadata such as course, module, and description.

### 5. Commits & Branches
- Name branches `feature/`, `fix/`, or `docs/` followed by scope.
- Keep commits short, imperative, and meaningful (e.g., `Add GPA validation`).
- Avoid noisy commit streams; group related changes together.

### 6. Testing & Checks
- Test UI changes on desktop, tablet, and mobile viewports.
- Ensure `python app.py` runs without errors.
- Validate calculators, timers, and forms for regressions.
- Run linters or formatters before submitting work.

### 7. Documentation
- Update `README.md` or in-app copy when behavior changes.
- Add screenshots or GIFs for visual updates (optimize size).
- Document new environment variables or configuration flags.

### 8. Pull Requests
- [ ] Rebase with `main` before opening the PR.
- [ ] Pass all tests and manual checks.
- [ ] Add clear before/after context (screenshots for UI).
- [ ] Link related issues and explain the fix.
- [ ] Respond to reviewer feedback promptly.

### 9. Reporting Issues
- Use descriptive titles and labels.
- Include reproduction steps, expected vs. actual results, and screenshots or logs.
- Tag issues appropriately (`bug`, `enhancement`, `docs`, etc.).

### 10. Community & License
- Be respectful, helpful, and open-minded in discussions and reviews.
- Contributions fall under `LICENSE.txt`.
- Attribute any third-party content you include.

Thank you for sharing your time and expertise with the students who rely on College Daddy!

