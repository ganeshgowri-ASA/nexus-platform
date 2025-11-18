# RPA Module Documentation

## Overview

The RPA (Robotic Process Automation) module provides comprehensive automation capabilities for the NEXUS platform, including desktop automation, process recording, UI element detection, and workflow orchestration.

## Architecture

### Components

1. **Automation Engine** (`engine.py`)
   - Core execution engine for running automation workflows
   - Parses workflow definitions and executes actions
   - Manages execution context and variables
   - Handles error recovery and retry logic

2. **Execution Manager** (`execution_manager.py`)
   - Creates and manages execution records
   - Tracks execution status and progress
   - Stores execution logs and results
   - Provides execution statistics

3. **Scheduler** (`scheduler.py`)
   - Manages scheduled automation executions
   - Supports cron expressions with timezone handling
   - Calculates next run times
   - Integrates with Celery Beat for scheduling

4. **Action Executors** (`actions.py`)
   - Implements individual action types
   - Supports: click, type, wait, conditions, loops, HTTP requests, data manipulation
   - Variable resolution and context management

5. **Process Recorder** (`recorder.py`)
   - Records user interactions (mouse, keyboard)
   - Converts recordings to workflow definitions
   - Saves/loads recorded sessions

6. **UI Element Detector** (`ui_detector.py`)
   - Detects UI elements using image matching
   - OCR-based text detection
   - Color detection and comparison
   - Screenshot capabilities

7. **Audit Logger** (`audit.py`)
   - Records all RPA actions
   - Provides audit trails
   - User activity tracking
   - Statistics and reporting

8. **Error Handler** (`error_handler.py`)
   - Custom RPA exception types
   - Retry logic configuration
   - Error severity levels
   - Decorator-based error handling

## Workflow Definition

Workflows are defined as JSON structures with nodes and edges:

```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "http_request",
      "name": "Fetch Data",
      "config": {
        "url": "https://api.example.com/data",
        "method": "GET",
        "store_as": "api_data"
      },
      "position": {"x": 100, "y": 0}
    },
    {
      "id": "node_2",
      "type": "log",
      "name": "Log Result",
      "config": {
        "message": "Data fetched: {{api_data}}",
        "level": "INFO"
      },
      "position": {"x": 100, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2"
    }
  ],
  "variables": {}
}
```

## Action Types

### Click Action
Simulates mouse clicks at specific coordinates.

```json
{
  "type": "click",
  "config": {
    "x": 100,
    "y": 200,
    "button": "left",
    "clicks": 1
  }
}
```

### Type Action
Simulates keyboard typing.

```json
{
  "type": "type",
  "config": {
    "text": "Hello World",
    "interval": 0.1
  }
}
```

### Wait Action
Pauses execution.

```json
{
  "type": "wait",
  "config": {
    "duration": 5
  }
}
```

### Condition Action
Evaluates conditions.

```json
{
  "type": "condition",
  "config": {
    "left": "{{variable}}",
    "operator": "==",
    "right": "expected_value",
    "store_as": "condition_result"
  }
}
```

### Loop Action
Iterates over collections.

```json
{
  "type": "loop",
  "config": {
    "items": ["item1", "item2", "item3"],
    "variable": "current_item"
  }
}
```

### HTTP Request Action
Makes API calls.

```json
{
  "type": "http_request",
  "config": {
    "url": "https://api.example.com/endpoint",
    "method": "POST",
    "data": {"key": "value"},
    "store_as": "response"
  }
}
```

### Data Manipulation Action
Transforms data.

```json
{
  "type": "data_manipulation",
  "config": {
    "operation": "parse_json",
    "data": "{{raw_data}}",
    "store_as": "parsed_data"
  }
}
```

**Supported Operations:**
- `parse_json` - Parse JSON string
- `to_json` - Convert to JSON string
- `split` - Split string
- `join` - Join array
- `uppercase` - Convert to uppercase
- `lowercase` - Convert to lowercase
- `trim` - Trim whitespace

## Variables

Variables can be used in action configurations using double curly braces:

```json
{
  "config": {
    "message": "Hello {{username}}, your ID is {{user_id}}"
  }
}
```

Variables are stored in the execution context and can be:
- Set using `set_variable` action
- Retrieved from previous action results
- Passed as input data
- Defined in workflow variables

## Error Handling

### Retry Configuration

```json
{
  "retry_config": {
    "enabled": true,
    "retryable_errors": ["TimeoutError", "ElementNotFoundError"],
    "strategy": "exponential",
    "base_delay": 5,
    "max_attempts": 3
  }
}
```

**Retry Strategies:**
- `fixed` - Fixed delay between retries
- `exponential` - Exponential backoff
- `linear` - Linear increase in delay

### Error Types

- `AutomationNotFoundError` - Automation does not exist
- `ExecutionError` - Execution failed
- `ValidationError` - Invalid input/configuration
- `TimeoutError` - Execution timeout
- `ElementNotFoundError` - UI element not found

## Scheduling

Create scheduled automations using cron expressions:

```python
# Daily at 9 AM
cron_expression = "0 9 * * *"

# Every hour
cron_expression = "0 * * * *"

# Every weekday at 6 PM
cron_expression = "0 18 * * 1-5"

# Every 15 minutes
cron_expression = "*/15 * * * *"
```

## API Usage Examples

### Create Bot

```bash
curl -X POST "http://localhost:8000/api/v1/rpa/bots" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web Scraper Bot",
    "description": "Scrapes data from websites",
    "bot_type": "ui_automation",
    "capabilities": ["web_scraping", "browser_automation"],
    "configuration": {"browser": "chromium"},
    "created_by": "admin"
  }'
```

### Create Automation

```bash
curl -X POST "http://localhost:8000/api/v1/rpa/automations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Report",
    "description": "Generates daily report",
    "trigger_type": "scheduled",
    "workflow": {
      "nodes": [...],
      "edges": [...],
      "variables": {}
    },
    "timeout": 3600,
    "created_by": "admin"
  }'
```

### Execute Automation

```bash
curl -X POST "http://localhost:8000/api/v1/rpa/automations/{id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "manual",
    "input_data": {"param1": "value1"},
    "triggered_by": "admin"
  }'
```

### Create Schedule

```bash
curl -X POST "http://localhost:8000/api/v1/rpa/schedules" \
  -H "Content-Type: application/json" \
  -d '{
    "automation_id": "{automation_id}",
    "name": "Daily Schedule",
    "cron_expression": "0 9 * * *",
    "timezone": "UTC",
    "input_data": {},
    "created_by": "admin"
  }'
```

## Best Practices

### Workflow Design

1. **Keep workflows modular** - Break complex workflows into smaller, reusable automations
2. **Use meaningful names** - Name nodes and variables descriptively
3. **Add logging** - Include log actions for debugging and monitoring
4. **Handle errors gracefully** - Configure retry logic and error handling
5. **Test thoroughly** - Test with various inputs before deploying

### Performance

1. **Use appropriate timeouts** - Set realistic timeout values
2. **Optimize loops** - Avoid unnecessary iterations
3. **Minimize waits** - Use the shortest wait times possible
4. **Batch operations** - Process items in batches when possible
5. **Clean up resources** - Properly close connections and free resources

### Security

1. **Validate inputs** - Always validate automation inputs
2. **Sanitize data** - Clean data before processing
3. **Use environment variables** - Store sensitive data in environment variables
4. **Audit regularly** - Review audit logs for suspicious activity
5. **Limit permissions** - Grant minimum necessary permissions

### Monitoring

1. **Check execution logs** - Regularly review execution logs
2. **Monitor success rates** - Track automation success/failure rates
3. **Set up alerts** - Configure alerts for failures
4. **Review performance** - Monitor execution times
5. **Analyze trends** - Look for patterns in failures

## Troubleshooting

### Common Issues

**Automation won't execute:**
- Check automation status is "active"
- Verify workflow definition is valid
- Check Celery workers are running
- Review execution logs for errors

**UI element not found:**
- Verify element selector is correct
- Check if UI has changed
- Use higher confidence threshold
- Add wait before element detection

**Timeout errors:**
- Increase timeout value
- Optimize workflow execution
- Check for infinite loops
- Review resource usage

**Schedule not running:**
- Verify cron expression is valid
- Check schedule is active
- Ensure Celery Beat is running
- Verify timezone settings

## Support

For more information:
- API Documentation: http://localhost:8000/docs
- Main README: ../README.md
- GitHub Issues: [repository]/issues
