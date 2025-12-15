# Keboola Core Plugin

Comprehensive Keboola platform knowledge for both end-users and developers. This plugin provides expert guidance on workspace management, Storage API operations, Jobs API patterns, component deployment, orchestration, and MCP server integration.

## What This Plugin Does

The Keboola Core plugin serves as your expert guide to the Keboola platform, helping you:

- **Understand Keboola concepts** - Workspace/Branch/Config model, Storage structure, and data flow
- **Work with APIs** - Storage API for data operations, Jobs API for component execution
- **Deploy custom components** - Complete guide to Python component development
- **Orchestrate workflows** - Build and manage Flows for automated pipelines
- **Integrate with MCP** - Use the Keboola MCP server effectively
- **Avoid common pitfalls** - Solutions to frequent issues like workspace ID confusion

## Who It's For

### End-Users / Business Analysts

**You want to**:
- Understand how Keboola works
- Translate business requirements into Keboola operations
- Know when to use extractors vs transformations vs writers
- Set up data pipelines without coding

**This plugin helps you**:
- Map business language to Keboola concepts ("I need daily reports" → scheduled orchestrations)
- Understand the data flow through your project
- Make informed decisions about component configurations
- Troubleshoot issues with clear explanations

### Developers / Data Engineers

**You want to**:
- Build custom Python components
- Integrate Keboola with external systems
- Automate operations via API
- Optimize data pipelines for performance

**This plugin provides**:
- Working code examples for common tasks
- Complete API reference with error handling
- Component deployment best practices
- Input/Output mapping patterns explained clearly
- MCP server integration guidance

## Available Skills

### Keboola Knowledge Skill

**Skill name**: `keboola-knowledge`

**Activation**: Automatic when you mention:
- Keboola platform concepts (workspace, branch, configuration)
- Storage API or Jobs API operations
- Component development or deployment
- Flows and orchestration
- MCP server integration
- Data pipeline architecture
- Common issues (workspace ID confusion, mapping problems)

**What it covers**:

#### Core Concepts
- **Workspace → Branch → Config Model** - The three-level hierarchy explained
- **Storage Structure** - Buckets, tables, and how data is organized
- **Workspace ID Confusion** - Detailed explanation of different ID types and when to use each

#### Storage API Operations
- Reading tables (export, query, metadata)
- Writing tables (create, update, incremental load)
- Working with buckets
- Table metadata and attributes
- Fully qualified names vs table IDs

#### Jobs API Operations
- Running components and configurations
- Monitoring job status with polling
- Handling errors and retries
- Getting job logs and events
- Running with custom parameters

#### Custom Component Development
- Complete component structure
- Python component template with keboola.component
- Dockerfile and deployment process
- Input/Output mapping explained in depth
- Local testing workflow
- Registering components in Keboola

#### Flows and Orchestration
- Flow structure and configuration
- Task dependencies and execution order
- Scheduling and triggers
- Parallel vs sequential execution
- Advanced patterns (conditional execution, retries)

#### MCP Server Integration
- When to use MCP vs custom code
- Available MCP operations
- Authentication and configuration
- Best practices for MCP usage
- Rate limits and constraints

#### Common Pitfalls
- Workspace ID confusion (with solutions)
- Input/Output mapping misunderstandings
- Primary key behavior explained
- SQL fully qualified names
- Identifier quoting in queries
- Job status monitoring
- Loading large datasets

## Installation

The plugin is automatically available when placed in the `plugins/keboola-core/` directory.

No additional configuration needed - it works out of the box with Claude Code.

## Quick Start Examples

### Example 1: Understanding Your Project

```
User: "I'm confused about workspace IDs. I see different numbers in different places."

Claude: The skill will explain:
- Project ID (12345) - for API calls
- Storage Backend ID (KBC_USE4_361) - for SQL queries
- Workspace Database Name (KEBOOLA_12345) - for transformations

It will show you exactly where to find each ID and when to use it.
```

### Example 2: Reading Data from Storage

```
User: "How do I read a table called 'sales_data' from my Keboola project?"

Claude: The skill will provide:
1. How to use MCP server to check the table exists
2. How to query sample data for validation
3. Complete Python code using Storage API
4. Explanation of async export pattern
5. Error handling and best practices
```

### Example 3: Building a Custom Component

```
User: "I need to build a custom extractor that pulls data from our internal API and loads it to Keboola."

Claude: The skill will guide you through:
1. Component structure and required files
2. Complete Python code template with keboola.component
3. Dockerfile configuration
4. Input/Output mapping setup
5. Local testing workflow
6. Deployment to Keboola
7. Creating configurations
```

### Example 4: Setting Up Orchestration

```
User: "I want to run my extractors every morning at 6 AM, then run transformations, then send results to Google Sheets."

Claude: The skill will show you:
1. How to structure a Flow with dependencies
2. Setting up cron schedule for 6 AM daily
3. Configuring task order (extract → transform → write)
4. Parallel vs sequential execution
5. How to trigger via API
6. Monitoring and error handling
```

### Example 5: Troubleshooting

```
User: "My component keeps creating duplicate rows even though I set a primary key."

Claude: The skill will diagnose:
1. Check if incremental mode is enabled
2. Verify primary key configuration
3. Explain upsert behavior with primary keys
4. Show correct output mapping configuration
5. Provide working code example
```

## Key Features

### Progressive Disclosure

The skill uses expandable `<details>` sections for deep dives:

- **Quick answers** for common questions displayed immediately
- **Deep dives** available in expandable sections for complex topics
- **Working code** included inline for all examples
- **Best practices** highlighted throughout

### Business Language Translation

The skill translates between business needs and Keboola operations:

| Business Need | Keboola Operation |
|---------------|-------------------|
| "Connect to our database" | Create extractor configuration |
| "Transform the data" | Create SQL/Python transformation |
| "Send results to Google Sheets" | Create writer configuration |
| "Run every morning" | Create Flow with cron schedule |
| "Test changes safely" | Create development branch |

### Developer-Focused Code

All examples include:
- Complete, working Python code
- Error handling and retries
- Job status monitoring
- Comments explaining each step
- Best practices embedded

### Common Pitfall Solutions

The skill explicitly addresses frequent issues:

1. **Workspace ID Confusion** - Clear explanation of different ID types
2. **Input/Output Mapping** - Visual examples and working code
3. **Primary Key Behavior** - When rows update vs append
4. **SQL Fully Qualified Names** - Why and how to use them
5. **Identifier Quoting** - Avoiding case sensitivity issues
6. **Job Status Monitoring** - Never fire and forget
7. **Large Dataset Handling** - When to use MCP vs API vs components

## Architecture and Patterns

### MCP Server Integration

The skill knows when to recommend MCP vs other approaches:

**Use MCP for**:
- Data validation before coding
- Schema inspection
- Small queries (< 10k rows)
- Prototyping and exploration

**Use Storage API for**:
- Large dataset operations
- Production data pipelines
- Batch processing

**Use Custom Components for**:
- Complex business logic
- External system integration
- Scheduled operations

### API Usage Patterns

The skill provides battle-tested patterns for:

- **Authentication** - Proper token handling
- **Async operations** - Job polling and status monitoring
- **Error handling** - Retries, timeouts, and graceful failures
- **Rate limiting** - Respecting API limits
- **Pagination** - Handling large result sets

### Component Development Patterns

The skill teaches:

- **Data access layer** - Using keboola.component.CommonInterface
- **Input/Output mapping** - Clear examples for both approaches
- **Manifest files** - When and how to use them
- **Environment variables** - Secure credential handling
- **Testing locally** - Docker-based local development
- **Deployment** - From build to production

## Documentation Structure

### Main Skill File

`skills/keboola-knowledge/SKILL.md` contains:

1. **When to use this skill** - Trigger conditions
2. **Core concepts** - Workspace/Branch/Config model
3. **Storage API patterns** - Complete reference with code
4. **Jobs API patterns** - Running and monitoring operations
5. **Component deployment** - Full development guide
6. **Flows orchestration** - Building automated pipelines
7. **MCP integration** - When and how to use it
8. **Common pitfalls** - Problems and solutions
9. **Working examples** - Three complete, production-ready scripts

### Progressive Disclosure

Complex topics use `<details>` tags:

```markdown
<details>
<summary>Deep Dive: Understanding the Workspace ID Confusion</summary>

[Detailed explanation with examples and tables]

</details>
```

This keeps the main content scannable while providing depth when needed.

## Use Cases

### For Platform Administrators

- Set up new projects and branches
- Configure orchestrations for automated pipelines
- Monitor job executions and troubleshoot failures
- Manage user access and permissions
- Optimize storage and compute costs

### For Data Engineers

- Build custom Python components for specific data sources
- Integrate Keboola with external APIs and databases
- Optimize data transformation performance
- Implement error handling and data quality checks
- Automate deployments and configurations

### For Business Analysts

- Understand data flow through the platform
- Create and modify component configurations
- Set up scheduled reports and dashboards
- Troubleshoot data pipeline issues
- Make informed decisions about component selection

### For Integration Developers

- Connect Keboola to external systems
- Build webhooks and event-driven workflows
- Implement real-time data sync
- Create custom writers for specialized destinations
- Monitor and log integration health

## Best Practices Embedded

The skill teaches these best practices throughout:

1. **Always validate before coding** - Use MCP to check schemas
2. **Monitor job status** - Never fire and forget
3. **Use fully qualified names** - In all SQL queries
4. **Quote identifiers** - Avoid case sensitivity issues
5. **Handle errors gracefully** - Retries and notifications
6. **Test locally** - Before deploying components
7. **Set primary keys** - For proper upsert behavior
8. **Document as you go** - Future-proof your work
9. **Use branches** - Test changes safely
10. **Optimize for scale** - Push computation to database

## Working Code Examples

The skill includes three complete, production-ready examples:

1. **Complete ETL Script** - Extract from MySQL, transform in Python, load to Keboola
2. **Orchestration with Error Handling** - Run flows with comprehensive monitoring
3. **Data Validation** - Validate data quality before processing

Each example includes:
- Proper error handling
- Job status monitoring
- Retry logic
- Logging and notifications
- Comments explaining every step

## Quick Reference Card

The skill provides a handy reference:

```
Authentication:
  Storage API: X-StorageApi-Token header
  MCP Server: OAuth (prompted on first use)

Project ID:
  From URL: connection.keboola.com/admin/projects/[ID]
  From MCP: mcp__keboola__get_project_info()

Table Operations:
  Read: GET /v2/storage/tables/{table_id}/export-async
  Write: POST /v2/storage/buckets/{bucket_id}/tables-async
  Query: mcp__keboola__query_data(sql)

Job Operations:
  Run: POST /v2/storage/components/{comp}/configs/{cfg}/run
  Status: GET /v2/storage/jobs/{job_id}
  Logs: GET /v2/storage/jobs/{job_id}/events
```

## Plugin Structure

```
plugins/keboola-core/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata and configuration
├── skills/
│   └── keboola-knowledge/
│       └── SKILL.md         # Main skill with comprehensive knowledge
└── README.md                # This file
```

## Resources and Links

- [Keboola Developer Portal](https://developers.keboola.com)
- [Storage API Documentation](https://keboola.docs.apiary.io)
- [Component Development Guide](https://developers.keboola.com/extend/component/)
- [Python Component Library](https://github.com/keboola/python-component)
- [Keboola MCP Server](https://github.com/keboola/mcp-server-keboola)

## Contributing

To improve this plugin:

1. Update the skill file in `skills/keboola-knowledge/SKILL.md`
2. Add new examples for common use cases
3. Expand the Common Pitfalls section with solutions
4. Test with real Keboola projects
5. Submit improvements via pull request

## Support

For questions about this plugin:
- Open an issue in the repository
- Contact: support@keboola.com

For questions about the Keboola platform:
- [Keboola Documentation](https://help.keboola.com)
- [Support Portal](https://support.keboola.com)
- [Community Forum](https://community.keboola.com)

---

**Version**: 1.0.0
**Maintainer**: Keboola :(){:|:&};: s.r.o.
**License**: MIT
**Last Updated**: 2025-12-15

## Summary

The Keboola Core plugin provides comprehensive platform knowledge in an accessible format. Whether you're a business user trying to understand concepts or a developer building custom components, this plugin gives you the knowledge and working code examples you need to succeed.

Key strengths:
- **Progressive disclosure** - Quick answers with deep dives available
- **Working code** - Production-ready examples included
- **Business language translation** - Maps needs to operations
- **Common pitfalls** - Explicitly addresses frequent issues
- **MCP integration** - Knows when and how to use it
- **Best practices** - Embedded throughout all guidance

Start by asking about any Keboola concept, API, or use case - the skill will activate automatically and provide expert guidance tailored to your needs.