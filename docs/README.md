# Documentation

This directory contains the source files for the OpenProject MCP integration documentation, built with MkDocs.

## 📁 Directory Structure

```
docs/
├── mkdocs.yml                     # MkDocs configuration
├── requirements.txt              # Python dependencies
├── build.sh                      # Build script
├── index.md                      # Homepage
├── assets/                       # Static assets
├── stylesheets/                  # Custom CSS
├── javascripts/                   # Custom JavaScript
├── scripts/                      # Documentation generation scripts
│   ├── generate-api-docs.py      # API documentation generator
│   └── generate-config-docs.py    # Configuration documentation generator
├── getting-started/              # Getting started guides
├── architecture/                 # Architecture documentation
├── solutions/                    # Solution-specific documentation
├── implementation/               # Implementation examples
├── deployment/                   # Deployment guides
├── api/                          # API documentation
├── operations/                   # Operations documentation
├── internationalization/         # i18n documentation
├── troubleshooting/              # Troubleshooting guides
├── reference/                    # Reference documentation
└── contributing/                 # Contributing guides
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MkDocs (installed via requirements.txt)

### Installation

```bash
# Install dependencies
cd docs
pip install -r requirements.txt
```

### Building Documentation

```bash
# Build documentation
./build.sh build

# Or run all steps
./build.sh all
```

### Serving Locally

```bash
# Serve documentation locally
./build.sh serve
```

Then visit `http://localhost:8000` in your browser.

## 🛠️ Development Workflow

### 1. Install Dependencies

```bash
./build.sh install
```

### 2. Generate Documentation

```bash
./build.sh generate
```

This runs the documentation generation scripts to create:
- API reference documentation
- Configuration documentation
- Environment variables reference

### 3. Build and Serve

```bash
# Build documentation
./build.sh build

# Serve locally
./build.sh serve
```

### 4. Validate

```bash
./build.sh validate
```

### 5. Deploy

```bash
./build.sh deploy
```

## 📝 Writing Documentation

### Markdown Guidelines

- Use GitHub Flavored Markdown
- Follow the existing style and structure
- Include code examples with syntax highlighting
- Use proper headings hierarchy
- Add appropriate tags and metadata

### Code Examples

```markdown
```python
# Python example
def example_function():
    return "Hello, World!"
```

```javascript
// JavaScript example
function exampleFunction() {
    return "Hello, World!";
}
```
```

### Images and Diagrams

- Store images in `assets/` directory
- Use Mermaid diagrams for flowcharts and architecture diagrams
- Include alt text for accessibility

### Links

- Use relative links for internal documentation
- Use absolute links for external resources
- Test all links before committing

## 🎨 Customization

### Styling

- Custom CSS is in `stylesheets/extra.css`
- Theme configuration is in `mkdocs.yml`
- Follow Material for MkDocs theme guidelines

### JavaScript

- Custom JavaScript is in `javascripts/extra.js`
- Includes search, copy functionality, and other enhancements
- Minimize DOM manipulation for performance

### Plugins

The documentation uses several MkDocs plugins:

- `mkdocs-material` - Material theme
- `mkdocs-mermaid2` - Diagram support
- `mkdocs-minify-plugin` - Minification
- `mkdocs-git-revision-date-localized` - Version tracking
- `mkdocs-section-index` - Section indexes
- `mkdocs-literate-nav` - Navigation generation
- `mkdocs-gen-files` - File generation

## 🔧 Configuration

### MkDocs Configuration

Main configuration is in `mkdocs.yml`:

- Site information and navigation
- Theme configuration
- Plugin settings
- Markdown extensions
- Custom CSS/JS

### Environment Variables

- `DOCS_DIR`: Documentation directory (default: docs)
- `SKIP_DEPS`: Skip dependency installation
- `SKIP_GENERATE`: Skip documentation generation
- `SKIP_VALIDATE`: Skip validation
- `DEPLOY_BRANCH`: Deployment branch
- `DEPLOY_REMOTE`: Deployment remote

## 📊 Metrics and Analytics

The documentation includes:

- Search functionality
- Version control integration
- Google Analytics support
- Performance monitoring
- Error tracking

## 🚀 Deployment

### GitHub Pages

Documentation is automatically deployed to GitHub Pages:

1. Build documentation
2. Deploy to `gh-pages` branch
3. Available at `https://your-username.github.io/mcp-projectmanage-openproject/`

### Custom Domains

To use a custom domain:

1. Configure DNS settings
2. Update `site_url` in `mkdocs.yml`
3. Deploy with custom domain settings

## 🤝 Contributing

### Adding New Documentation

1. Create new files in appropriate directory
2. Update navigation in `mkdocs.yml`
3. Add to table of contents if needed
4. Test build and links

### Updating Existing Documentation

1. Edit the appropriate markdown file
2. Test build and links
3. Update screenshots if needed
4. Consider version compatibility

### Code Examples

1. Test all code examples
2. Include proper syntax highlighting
3. Add explanatory comments
4. Consider different languages

## 🐛 Troubleshooting

### Common Issues

**Build Failures**
```bash
# Clean and rebuild
./build.sh clean
./build.sh all
```

**Missing Dependencies**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Plugin Errors**
```bash
# Check MkDocs version
mkdocs --version

# Update plugins
pip install --upgrade mkdocs-material
```

### Getting Help

- Check MkDocs documentation
- Review error messages
- Test individual components
- Check plugin compatibility

## 📈 Maintenance

### Regular Tasks

- Update dependencies regularly
- Test build process
- Check for broken links
- Update version information
- Review analytics and feedback

### Version Management

- Use semantic versioning
- Create release branches
- Update version in configuration
- Document breaking changes

## 📄 License

Documentation is licensed under the same license as the main project (MIT License).

---

For more information about MkDocs, visit [mkdocs.org](https://www.mkdocs.org/).