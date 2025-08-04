---
quickstart.ipynb
---

# LangGraph.js - Quickstart

## Introduction

In this quickstart guide, you'll get up and running with a simple Reason + Act Agent (often
called a ReAct Agent) that can search the web using [Tavily Search API](https://tavily.com/).
The code is fully configurable. You can:

- swap out components
- customize the execution flow
- extend it with custom code or tooling
- change the Large Language Model (LLM) and provider being used


## Prerequisites

To follow along, you'll need to have the following:

- NodeJS version 18 or newer
- A [Tavily](https://tavily.com/) account and API key
- An [OpenAI developer platform](https://platform.openai.com/docs/overview) account and API key

Start by creating a new folder for the project. Open your terminal and run the following code:

```bash
mkdir langgraph-agent
cd langgraph-agent
```

You'll also need to install a few dependencies to create an agent:

- **`@langchain/langgraph`** contains the building blocks used to assemble an agent
- **`@langchain/openai`** enable your agent to use OpenAI's LLMs
- **`@langchain/community`** includes the Tavily integration give your agent search capabilities

You can install these dependencies using by running following npm command in your terminal:

```bash
npm install @langchain/core @langchain/langgraph @langchain/openai @langchain/community
```

## LangSmith

Optionally, set up [LangSmith](https://docs.smith.langchain.com/) for best-in-class observability. Setup is simple - add the following variables to your environment and update the `LANGCHAIN_API_KEY` value with your API key.


```typescript
// Optional, add tracing in LangSmith
// process.env.LANGCHAIN_API_KEY = "ls__...";
// process.env.LANGCHAIN_CALLBACKS_BACKGROUND = "true";
// process.env.LANGCHAIN_TRACING_V2 = "true";
// process.env.LANGCHAIN_PROJECT = "Quickstart: LangGraphJS";

```

## Making your first agent using LangGraph

Create a file named `agent.mts` (short for Reason + Act Agent) and add the below TypeScript code to it.

Make sure you update the environment variables at the top of the file to contain your API keys. If you don't, the OpenAI and Tavily API calls will produce errors and your agent will not work correctly.

Once you've added your API keys, save the file and run the code with the following command:

```bash
npx tsx agent.mts
```


```typescript
// agent.mts

// IMPORTANT - Add your API keys here. Be careful not to publish them.
process.env.OPENAI_API_KEY = "sk-...";
process.env.TAVILY_API_KEY = "tvly-...";

import { TavilySearchResults } from "@langchain/community/tools/tavily_search";
import { ChatOpenAI } from "@langchain/openai";
import { MemorySaver } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

// Define the tools for the agent to use
const agentTools = [new TavilySearchResults({ maxResults: 3 })];
const agentModel = new ChatOpenAI({ temperature: 0 });

// Initialize memory to persist state between graph runs
const agentCheckpointer = new MemorySaver();
const agent = createReactAgent({
  llm: agentModel,
  tools: agentTools,
  checkpointSaver: agentCheckpointer,
});

// Now it's time to use!
const agentFinalState = await agent.invoke(
  { messages: [new HumanMessage("what is the current weather in sf")] },
  { configurable: { thread_id: "42" } },
);

console.log(
  agentFinalState.messages[agentFinalState.messages.length - 1].content,
);

const agentNextState = await agent.invoke(
  { messages: [new HumanMessage("what about ny")] },
  { configurable: { thread_id: "42" } },
);

console.log(
  agentNextState.messages[agentNextState.messages.length - 1].content,
);
```
```output
The current weather in San Francisco is as follows:
- Temperature: 82.0°F (27.8°C)
- Condition: Sunny
- Wind: 11.9 mph from the NW
- Humidity: 41%
- Pressure: 29.98 in
- Visibility: 9.0 miles
- UV Index: 6.0

For more details, you can visit [Weather in San Francisco](https://www.weatherapi.com/).
The current weather in New York is as follows:
- Temperature: 84.0°F (28.9°C)
- Condition: Sunny
- Wind: 2.2 mph from SSE
- Humidity: 57%
- Pressure: 29.89 in
- Precipitation: 0.01 in
- Visibility: 9.0 miles
- UV Index: 6.0

For more details, you can visit [Weather in New York](https://www.weatherapi.com/).
```
## How does it work?

The
<a href="/langgraphjs/reference/functions/langgraph_prebuilt.createReactAgent.html">createReactAgent</a>
constructor lets you create a simple tool-using LangGraph agent in a single line
of code. Here's a visual representation of the graph:


```typescript
// Note: tslab only works inside a jupyter notebook. Don't worry about running this code yourself!
import * as tslab from "tslab";

const graph = agent.getGraph();
const image = await graph.drawMermaidPng();
const arrayBuffer = await image.arrayBuffer();

await tslab.display.png(new Uint8Array(arrayBuffer));
```



Alternatively, you can save the graph as a PNG file locally using the following approach:

```ts
import { writeFileSync } from "node:fs";

const graphStateImage = await drawableGraphGraphState.drawMermaidPng();
const graphStateArrayBuffer = await graphStateImage.arrayBuffer();

const filePath = "./graphState.png";
writeFileSync(filePath, new Uint8Array(graphStateArrayBuffer));
```


## Customizing agent behavior

createReactAgent can be great for simple agents, but sometimes you need something more powerful.

LangGraph really shines when you need fine-grained control over an agent's behavior. The following
code creates an agent with the same behavior as the example above, but you can
clearly see the execution logic and how you could customize it.

Update the code in your `agent.mts` file to match the example below. Once again, be sure to update
the environment variables at the top.

After you've updated your environment variables and saved the file, you can run it with the same command as before:

```bash
npx tsx agent.mts
```


```typescript
// agent.mts

// IMPORTANT - Add your API keys here. Be careful not to publish them.
process.env.OPENAI_API_KEY = "sk-...";
process.env.TAVILY_API_KEY = "tvly-...";

import { TavilySearchResults } from "@langchain/community/tools/tavily_search";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, AIMessage } from "@langchain/core/messages";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { StateGraph, MessagesAnnotation } from "@langchain/langgraph";

// Define the tools for the agent to use
const tools = [new TavilySearchResults({ maxResults: 3 })];
const toolNode = new ToolNode(tools);

// Create a model and give it access to the tools
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  temperature: 0,
}).bindTools(tools);

// Define the function that determines whether to continue or not
function shouldContinue({ messages }: typeof MessagesAnnotation.State) {
  const lastMessage = messages[messages.length - 1] as AIMessage;

  // If the LLM makes a tool call, then we route to the "tools" node
  if (lastMessage.tool_calls?.length) {
    return "tools";
  }
  // Otherwise, we stop (reply to the user) using the special "__end__" node
  return "__end__";
}

// Define the function that calls the model
async function callModel(state: typeof MessagesAnnotation.State) {
  const response = await model.invoke(state.messages);

  // We return a list, because this will get added to the existing list
  return { messages: [response] };
}

// Define a new graph
const workflow = new StateGraph(MessagesAnnotation)
  .addNode("agent", callModel)
  .addEdge("__start__", "agent") // __start__ is a special name for the entrypoint
  .addNode("tools", toolNode)
  .addEdge("tools", "agent")
  .addConditionalEdges("agent", shouldContinue);

// Finally, we compile it into a LangChain Runnable.
const app = workflow.compile();

// Use the agent
const finalState = await app.invoke({
  messages: [new HumanMessage("what is the weather in sf")],
});
console.log(finalState.messages[finalState.messages.length - 1].content);

const nextState = await app.invoke({
  // Including the messages from the previous run gives the LLM context.
  // This way it knows we're asking about the weather in NY
  messages: [...finalState.messages, new HumanMessage("what about ny")],
});
console.log(nextState.messages[nextState.messages.length - 1].content);
```

There are a few new things going on in this version of our ReAct Agent.

A [`ToolNode`](https://langchain-ai.github.io/langgraphjs/reference/classes/langgraph_prebuilt.ToolNode.html) enables the LLM to use tools.
In this example, we made a `shouldContinue` function and passed it to [`addConditionalEdge`](https://langchain-ai.github.io/langgraphjs/reference/classes/langgraph.StateGraph.html#addConditionalEdges) so our ReAct Agent can either call a tool or respond to the request.

[Annotations](https://langchain-ai.github.io/langgraphjs/concepts/low_level/#annotation) are how graph state is represented in LangGraph. We're using [`MessagesAnnotation`](https://langchain-ai.github.io/langgraphjs/concepts/low_level/#messagesannotation), a helper that implements a common pattern: keeping the message history in an array.

## Next Steps

Great job creating your first AI agent using LangGraph! If you're ready to build
something more, check out our other <a href="/langgraphjs/tutorials/">tutorials</a>
to learn how to implement other end-to-end agentic workflows such as:

- <a href="/langgraphjs/tutorials/rag/langgraph_agentic_rag/">Retrieval-Augmented Generation (RAG)</a>
- <a href="/langgraphjs/tutorials/multi_agent/multi_agent_collaboration/">Multi-agent collaboration</a>
- <a href="/langgraphjs/tutorials/reflection/reflection/">Reflection</a>, where the agent evaluates its work

If you'd rather improve your agent we have <a href="/langgraphjs/how-tos/">how-to guides</a> to help, including:

- <a href="/langgraphjs/how-tos/tool-calling/">Tool calling</a> that enables agents to interact with APIs
- give your agent <a href="/langgraphjs/how-tos/persistence/">persistent memory</a> to continue conversations and debug unexpected behavior
- Put a <a href="/langgraphjs/how-tos/breakpoints/">human in the loop</a> for actions you want a human to verify
- <a href="/langgraphjs/how-tos/stream-values/">Streaming the agent output</a> to make your application feel more responsive
- [Change the AI model in one line of code](https://js.langchain.com/docs/how_to/chat_models_universal_init/)



---
how-tos/index.md
---

---
title: How-to Guides
description: How to accomplish common tasks in LangGraph.js
---

# How-to guides

Here you’ll find answers to “How do I...?” types of questions. These guides are **goal-oriented** and concrete; they're meant to help you complete a specific task. For conceptual explanations see the [Conceptual guide](../concepts/index.md). For end-to-end walk-throughs see [Tutorials](../tutorials/index.md). For comprehensive descriptions of every class and function see the [API Reference](https://langchain-ai.github.io/langgraphjs/reference/).

## Installation

- [How to install and manage dependencies](manage-ecosystem-dependencies.ipynb)
- [How to use LangGraph.js in web environments](use-in-web-environments.ipynb)

## LangGraph

### Controllability

LangGraph.js is known for being a highly controllable agent framework.
These how-to guides show how to achieve that controllability.

- [How to create branches for parallel execution](branching.ipynb)
- [How to create map-reduce branches for parallel execution](map-reduce.ipynb)
- [How to defer node execution](defer-node-execution.ipynb)
- [How to combine control flow and state updates with Command](command.ipynb)
- [How to create and control loops with recursion limits](recursion-limit.ipynb)

### Persistence

LangGraph.js makes it easy to persist state across graph runs. The guides below shows how to add persistence to your graph.

- [How to add thread-level persistence to your graph](persistence.ipynb)
- [How to add thread-level persistence to subgraphs](subgraph-persistence.ipynb)
- [How to add cross-thread persistence](cross-thread-persistence.ipynb)
- [How to use a Postgres checkpointer for persistence](persistence-postgres.ipynb)

See the below guides for how-to add persistence to your workflow using the [Functional API](../concepts/functional_api.md):

- [How to add thread-level persistence (functional API)](persistence-functional.ipynb)
- [How to add cross-thread persistence (functional API)](cross-thread-persistence-functional.ipynb)

### Memory

LangGraph makes it easy to manage conversation [memory](../concepts/memory.md) in your graph. These how-to guides show how to implement different strategies for that.

- [How to manage conversation history](manage-conversation-history.ipynb)
- [How to delete messages](delete-messages.ipynb)
- [How to add summary of the conversation history](add-summary-conversation-history.ipynb)
- [How to add long-term memory (cross-thread)](cross-thread-persistence.ipynb)
- [How to use semantic search for long-term memory](semantic-search.ipynb)

### Human-in-the-loop

[Human-in-the-loop](/langgraphjs/concepts/human_in_the_loop) functionality allows
you to involve humans in the decision-making process of your graph. These how-to guides show how to implement human-in-the-loop workflows in your graph.

Key workflows:

- [How to wait for user input](wait-user-input.ipynb): A basic example that shows how to implement a human-in-the-loop workflow in your graph using the `interrupt` function.
- [How to review tool calls](review-tool-calls.ipynb): Incorporate human-in-the-loop for reviewing/editing/accepting tool call requests before they executed using the `interrupt` function.

Other methods:

- [How to add static breakpoints](breakpoints.ipynb): Use for debugging purposes. For [**human-in-the-loop**](/langgraphjs/concepts/human_in_the_loop) workflows, we recommend the [`interrupt` function](/langgraphjs/reference/functions/langgraph.interrupt-1.html) instead.
- [How to edit graph state](edit-graph-state.ipynb): Edit graph state using `graph.update_state` method. Use this if implementing a **human-in-the-loop** workflow via **static breakpoints**.
- [How to add dynamic breakpoints with `NodeInterrupt`](dynamic_breakpoints.ipynb): **Not recommended**: Use the [`interrupt` function](/langgraphjs/concepts/human_in_the_loop) instead.

See the below guides for how-to implement human-in-the-loop workflows with the [Functional API](../concepts/functional_api.md):

- [How to wait for user input (Functional API)](wait-user-input-functional.ipynb)
- [How to review tool calls (Functional API)](review-tool-calls-functional.ipynb)

### Time Travel

[Time travel](../concepts/time-travel.md) allows you to replay past actions in your LangGraph application to explore alternative paths and debug issues. These how-to guides show how to use time travel in your graph.

- [How to view and update past graph state](time-travel.ipynb)

### Streaming

LangGraph is built to be streaming first.
These guides show how to use different streaming modes.

- [How to stream the full state of your graph](stream-values.ipynb)
- [How to stream state updates of your graph](stream-updates.ipynb)
- [How to stream LLM tokens](stream-tokens.ipynb)
- [How to stream LLM tokens without LangChain models](streaming-tokens-without-langchain.ipynb)
- [How to stream custom data](streaming-content.ipynb)
- [How to configure multiple streaming modes](stream-multiple.ipynb)
- [How to stream events from within a tool](streaming-events-from-within-tools.ipynb)
- [How to stream from the final node](streaming-from-final-node.ipynb)

### Tool calling

- [How to call tools using ToolNode](tool-calling.ipynb)
- [How to force an agent to call a tool](force-calling-a-tool-first.ipynb)
- [How to handle tool calling errors](tool-calling-errors.ipynb)
- [How to pass runtime values to tools](pass-run-time-values-to-tools.ipynb)
- [How to update graph state from tools](update-state-from-tools.ipynb)

### Subgraphs

[Subgraphs](../concepts/low_level.md#subgraphs) allow you to reuse an existing graph from another graph. These how-to guides show how to use subgraphs:

- [How to add and use subgraphs](subgraph.ipynb)
- [How to view and update state in subgraphs](subgraphs-manage-state.ipynb)
- [How to transform inputs and outputs of a subgraph](subgraph-transform-state.ipynb)

### Multi-agent

- [How to build a multi-agent network](multi-agent-network.ipynb)
- [How to add multi-turn conversation in a multi-agent application](multi-agent-multi-turn-convo.ipynb)

See the [multi-agent tutorials](../tutorials/index.md#multi-agent-systems) for implementations of other multi-agent architectures.

See the below guides for how-to implement multi-agent workflows with the [Functional API](../concepts/functional_api.md):

- [How to build a multi-agent network (functional API)](multi-agent-network-functional.ipynb)
- [How to add multi-turn conversation in a multi-agent application (functional API)](multi-agent-multi-turn-convo-functional.ipynb)

### State management

- [How to define graph state](define-state.ipynb)
- [Have a separate input and output schema](input_output_schema.ipynb)
- [Pass private state between nodes inside the graph](pass_private_state.ipynb)

### Other

- [How to add runtime configuration to your graph](configuration.ipynb)
- [How to add node retries](node-retry-policies.ipynb)
- [How to cache expensive nodes](node-caching.ipynb)
- [How to let an agent return tool results directly](dynamically-returning-directly.ipynb)
- [How to have an agent respond in structured format](respond-in-format.ipynb)
- [How to manage agent steps](managing-agent-steps.ipynb)

### Prebuilt ReAct Agent

- [How to create a ReAct agent](create-react-agent.ipynb)
- [How to add memory to a ReAct agent](react-memory.ipynb)
- [How to add a system prompt to a ReAct agent](react-system-prompt.ipynb)
- [How to add Human-in-the-loop to a ReAct agent](react-human-in-the-loop.ipynb)
- [How to return structured output from a ReAct agent](react-return-structured-output.ipynb)

See the below guide for how-to build ReAct agents with the [Functional API](../concepts/functional_api.md):

- [How to create a ReAct agent from scratch (Functional API)](react-agent-from-scratch-functional.ipynb)

## LangGraph Platform

This section includes how-to guides for LangGraph Platform.

LangGraph Platform is a commercial solution for deploying agentic applications in production, built on the open-source LangGraph framework. It provides four deployment options to fit a range of needs: a free tier, a self-hosted version, a cloud SaaS, and a Bring Your Own Cloud (BYOC) option. You can explore these options in detail in the [deployment options guide](../concepts/deployment_options.md).

!!! tip

    * LangGraph is an MIT-licensed open-source library, which we are committed to maintaining and growing for the community.
    * You can always deploy LangGraph applications on your own infrastructure using the open-source LangGraph project without using LangGraph Platform.

### Application Structure

Learn how to set up your app for deployment to LangGraph Platform:

- [How to set up app for deployment (requirements.txt)](/langgraphjs/cloud/deployment/setup)
- [How to set up app for deployment (pyproject.toml)](/langgraphjs/cloud/deployment/setup_pyproject)
- [How to set up app for deployment (JavaScript)](/langgraphjs/cloud/deployment/setup_javascript)
- [How to customize Dockerfile](/langgraphjs/cloud/deployment/custom_docker)
- [How to test locally](/langgraphjs/cloud/deployment/test_locally)
- [How to integrate LangGraph into your React application](/langgraphjs/cloud/how-tos/use_stream_react)

### Deployment

LangGraph applications can be deployed using LangGraph Cloud, which provides a range of services to help you deploy, manage, and scale your applications.

- [How to deploy to LangGraph cloud](/langgraphjs/cloud/deployment/cloud)
- [How to deploy to a self-hosted environment](./deploy-self-hosted.md)
- [How to interact with the deployment using RemoteGraph](./use-remote-graph.md)

### Authentication & Access Control

- [How to add custom authentication](./auth/custom_auth.md)

### Modifying the API

- [How to add custom routes](./http/custom_routes.md)
- [How to add custom middleware](./http/custom_middleware.md)

### Assistants

[Assistants](../concepts/assistants.md) are a configured instance of a template.

- [How to configure agents](/langgraphjs/cloud/how-tos/configuration_cloud)
- [How to version assistants](/langgraphjs/cloud/how-tos/assistant_versioning)

### Threads

- [How to copy threads](/langgraphjs/cloud/how-tos/copy_threads)
- [How to check status of your threads](/langgraphjs/cloud/how-tos/check_thread_status)

### Runs

LangGraph Cloud supports multiple types of runs besides streaming runs.

- [How to run an agent in the background](/langgraphjs/cloud/how-tos/background_run)
- [How to run multiple agents in the same thread](/langgraphjs/cloud/how-tos/same-thread)
- [How to create cron jobs](/langgraphjs/cloud/how-tos/cron_jobs)
- [How to create stateless runs](/langgraphjs/cloud/how-tos/stateless_runs)

### Streaming

Streaming the results of your LLM application is vital for ensuring a good user experience, especially when your graph may call multiple models and take a long time to fully complete a run. Read about how to stream values from your graph in these how to guides:

- [How to stream values](/langgraphjs/cloud/how-tos/stream_values)
- [How to stream updates](/langgraphjs/cloud/how-tos/stream_updates)
- [How to stream messages](/langgraphjs/cloud/how-tos/stream_messages)
- [How to stream events](/langgraphjs/cloud/how-tos/stream_events)
- [How to stream in debug mode](/langgraphjs/cloud/how-tos/stream_debug)
- [How to stream multiple modes](/langgraphjs/cloud/how-tos/stream_multiple)

### Frontend & Generative UI

With LangGraph Platform you can integrate LangGraph agents into your React applications and colocate UI components with your agent code.

- [How to integrate LangGraph into your React application](/langgraphjs/cloud/how-tos/use_stream_react)
- [How to implement Generative User Interfaces with LangGraph](/langgraphjs/cloud/how-tos/generative_ui_react)

### Human-in-the-loop

When creating complex graphs, leaving every decision up to the LLM can be dangerous, especially when the decisions involve invoking certain tools or accessing specific documents. To remedy this, LangGraph allows you to insert human-in-the-loop behavior to ensure your graph does not have undesired outcomes. Read more about the different ways you can add human-in-the-loop capabilities to your LangGraph Cloud projects in these how-to guides:

- [How to add a breakpoint](/langgraphjs/cloud/how-tos/human_in_the_loop_breakpoint)
- [How to wait for user input](/langgraphjs/cloud/how-tos/human_in_the_loop_user_input)
- [How to edit graph state](/langgraphjs/cloud/how-tos/human_in_the_loop_edit_state)
- [How to replay and branch from prior states](/langgraphjs/cloud/how-tos/human_in_the_loop_time_travel)
- [How to review tool calls](/langgraphjs/cloud/how-tos/human_in_the_loop_review_tool_calls)

### Double-texting

Graph execution can take a while, and sometimes users may change their mind about the input they wanted to send before their original input has finished running. For example, a user might notice a typo in their original request and will edit the prompt and resend it. Deciding what to do in these cases is important for ensuring a smooth user experience and preventing your graphs from behaving in unexpected ways. The following how-to guides provide information on the various options LangGraph Cloud gives you for dealing with double-texting:

- [How to use the interrupt option](/langgraphjs/cloud/how-tos/interrupt_concurrent)
- [How to use the rollback option](/langgraphjs/cloud/how-tos/rollback_concurrent)
- [How to use the reject option](/langgraphjs/cloud/how-tos/reject_concurrent)
- [How to use the enqueue option](/langgraphjs/cloud/how-tos/enqueue_concurrent)

### Webhooks

- [How to integrate webhooks](/langgraphjs/cloud/how-tos/webhooks)

### Cron Jobs

- [How to create cron jobs](/langgraphjs/cloud/how-tos/cron_jobs)

### LangGraph Studio

LangGraph Studio is a built-in UI for visualizing, testing, and debugging your agents.

- [How to connect to a LangGraph Cloud deployment](/langgraphjs/cloud/how-tos/test_deployment)
- [How to connect to a local deployment](/langgraphjs/cloud/how-tos/test_local_deployment)
- [How to test your graph in LangGraph Studio](/langgraphjs/cloud/how-tos/invoke_studio)
- [How to interact with threads in LangGraph Studio](/langgraphjs/cloud/how-tos/threads_studio)

## Troubleshooting

These are the guides for resolving common errors you may find while building with LangGraph. Errors referenced below will have an `lc_error_code` property corresponding to one of the below codes when they are thrown in code.

- [GRAPH_RECURSION_LIMIT](../troubleshooting/errors/GRAPH_RECURSION_LIMIT.ipynb)
- [INVALID_CONCURRENT_GRAPH_UPDATE](../troubleshooting/errors/INVALID_CONCURRENT_GRAPH_UPDATE.ipynb)
- [INVALID_GRAPH_NODE_RETURN_VALUE](../troubleshooting/errors/INVALID_GRAPH_NODE_RETURN_VALUE.ipynb)
- [MULTIPLE_SUBGRAPHS](../troubleshooting/errors/MULTIPLE_SUBGRAPHS.ipynb)
- [UNREACHABLE_NODE](../troubleshooting/errors/UNREACHABLE_NODE.ipynb)


---
how-tos/use-remote-graph.md
---

# How to interact with the deployment using RemoteGraph

!!! info "Prerequisites"
    - [LangGraph Platform](../concepts/langgraph_platform.md)
    - [LangGraph Server](../concepts/langgraph_server.md)

`RemoteGraph` is an interface that allows you to interact with your LangGraph Platform deployment as if it were a regular, locally-defined LangGraph graph (e.g. a `CompiledGraph`). This guide shows you how you can initialize a `RemoteGraph` and interact with it.

## Initializing the graph

When initializing a `RemoteGraph`, you must always specify:

- `name`: the name of the graph you want to interact with. This is the same graph name you use in `langgraph.json` configuration file for your deployment. 
- `api_key`: a valid LangSmith API key. Can be set as an environment variable (`LANGSMITH_API_KEY`) or passed directly via the `api_key` argument. The API key could also be provided via the `client` / `sync_client` arguments, if `LangGraphClient` / `SyncLangGraphClient` were initialized with `api_key` argument.

Additionally, you have to provide one of the following:

- `url`: URL of the deployment you want to interact with. If you pass `url` argument, both sync and async clients will be created using the provided URL, headers (if provided) and default configuration values (e.g. timeout, etc).
- `client`: a `LangGraphClient` instance for interacting with the deployment asynchronously (e.g. using `.astream()`, `.ainvoke()`, `.aget_state()`, `.aupdate_state()`, etc.)
- `sync_client`: a `SyncLangGraphClient` instance for interacting with the deployment synchronously (e.g. using `.stream()`, `.invoke()`, `.get_state()`, `.update_state()`, etc.)

!!! Note

    If you pass both `client` or `sync_client` as well as `url` argument, they will take precedence over the `url` argument. If none of the `client` / `sync_client` / `url` arguments are provided, `RemoteGraph` will raise a `ValueError` at runtime.


### Using URL

=== "Python"

    ```python
    from langgraph.pregel.remote import RemoteGraph

    url = <DEPLOYMENT_URL>
    graph_name = "agent"
    remote_graph = RemoteGraph(graph_name, url=url)
    ```

=== "JavaScript"

    ```ts
    import { RemoteGraph } from "@langchain/langgraph/remote";

    const url = `<DEPLOYMENT_URL>`;
    const graphName = "agent";
    const remoteGraph = new RemoteGraph({ graphId: graphName, url });
    ```

### Using clients

=== "Python"

    ```python
    from langgraph_sdk import get_client, get_sync_client
    from langgraph.pregel.remote import RemoteGraph

    url = <DEPLOYMENT_URL>
    graph_name = "agent"
    client = get_client(url=url)
    sync_client = get_sync_client(url=url)
    remote_graph = RemoteGraph(graph_name, client=client, sync_client=sync_client)
    ```

=== "JavaScript"

    ```ts
    import { Client } from "@langchain/langgraph-sdk";
    import { RemoteGraph } from "@langchain/langgraph/remote";

    const client = new Client({ apiUrl: `<DEPLOYMENT_URL>` });
    const graphName = "agent";
    const remoteGraph = new RemoteGraph({ graphId: graphName, client });
    ```

## Invoking the graph

Since `RemoteGraph` is a `Runnable` that implements the same methods as `CompiledGraph`, you can interact with it the same way you normally would with a compiled graph, i.e. by calling `.invoke()`, `.stream()`, `.get_state()`, `.update_state()`, etc (as well as their async counterparts).

### Asynchronously

!!! Note

    To use the graph asynchronously, you must provide either the `url` or `client` when initializing the `RemoteGraph`.

=== "Python"

    ```python
    # invoke the graph
    result = await remote_graph.ainvoke({
        "messages": [{"role": "user", "content": "what's the weather in sf"}]
    })

    # stream outputs from the graph
    async for chunk in remote_graph.astream({
        "messages": [("user", "what's the weather in la?")]
    }):
        print(chunk)
    ```

=== "JavaScript"

    ```ts
    // invoke the graph
    const result = await remoteGraph.invoke({
        messages: [{role: "user", content: "what's the weather in sf"}]
    })

    // stream outputs from the graph
    for await (const chunk of await remoteGraph.stream({
        messages: [{role: "user", content: "what's the weather in la"}]
    })):
        console.log(chunk)
    ```

### Synchronously

!!! Note

    To use the graph synchronously, you must provide either the `url` or `sync_client` when initializing the `RemoteGraph`.

=== "Python"

    ```python
    # invoke the graph
    result = remote_graph.invoke({
        "messages": [{"role": "user", "content": "what's the weather in sf"}]
    })

    # stream outputs from the graph
    for chunk in remote_graph.stream({
        "messages": [("user", "what's the weather in la?")]
    }):
        print(chunk)
    ```

## Thread-level persistence

By default, the graph runs (i.e. `.invoke()` or `.stream()` invocations) are stateless - the checkpoints and the final state of the graph are not persisted. If you would like to persist the outputs of the graph run (for example, to enable human-in-the-loop features), you can create a thread and provide the thread ID via the `config` argument, same as you would with a regular compiled graph:

=== "Python"

    ```python
    from langgraph_sdk import get_sync_client
    url = <DEPLOYMENT_URL>
    graph_name = "agent"
    sync_client = get_sync_client(url=url)
    remote_graph = RemoteGraph(graph_name, url=url)

    # create a thread (or use an existing thread instead)
    thread = sync_client.threads.create()

    # invoke the graph with the thread config
    config = {"configurable": {"thread_id": thread["thread_id"]}}
    result = remote_graph.invoke({
        "messages": [{"role": "user", "content": "what's the weather in sf"}], config=config
    })

    # verify that the state was persisted to the thread
    thread_state = remote_graph.get_state(config)
    print(thread_state)
    ```

=== "JavaScript"

    ```ts
    import { Client } from "@langchain/langgraph-sdk";
    import { RemoteGraph } from "@langchain/langgraph/remote";

    const url = `<DEPLOYMENT_URL>`;
    const graphName = "agent";
    const client = new Client({ apiUrl: url });
    const remoteGraph = new RemoteGraph({ graphId: graphName, url });

    // create a thread (or use an existing thread instead)
    const thread = await client.threads.create();

    // invoke the graph with the thread config
    const config = { configurable: { thread_id: thread.thread_id }};
    const result = await remoteGraph.invoke({
      messages: [{ role: "user", content: "what's the weather in sf" }],
      config
    });

    // verify that the state was persisted to the thread
    const threadState = await remoteGraph.getState(config);
    console.log(threadState);
    ```

## Using as a subgraph
# How to stream LLM tokens from your graph

In this example, we will stream tokens from the language model powering an
agent. We will use a ReAct agent as an example.

<div class="admonition info">
    <p class="admonition-title">Note</p>
    <p>
      If you are using a version of <code>@langchain/core</code> < 0.2.3, when calling chat models or LLMs you need to call <code>await model.stream()</code> within your nodes to get token-by-token streaming events, and aggregate final outputs if needed to update the graph state. In later versions of <code>@langchain/core</code>, this occurs automatically, and you can call <code>await model.invoke()</code>.
      <br>
      For more on how to upgrade <code>@langchain/core</code>, check out <a href="https://js.langchain.com/docs/how_to/installation/#installing-integration-packages">the instructions here</a>.
    </p>
</div>

This how-to guide closely follows the others in this directory, showing how to
incorporate the functionality into a prototypical agent in LangGraph.

<div class="admonition info">
    <p class="admonition-title">Streaming Support</p>
    <p>
        Token streaming is supported by many, but not all chat models. Check to see if your LLM integration supports token streaming <a href="https://js.langchain.com/docs/integrations/chat/">here (doc)</a>. Note that some integrations may support <i>general</i> token streaming but lack support for streaming tool calls.
    </p>
</div>

<div class="admonition tip">
    <p class="admonition-title">Note</p>
    <p>
        In this how-to, we will create our agent from scratch to be transparent (but verbose). You can accomplish similar functionality using the <code>createReactAgent({ llm, tools })</code> (<a href="/langgraphjs/reference/functions/langgraph_prebuilt.createReactAgent.html">API doc</a>) constructor. This may be more appropriate if you are used to LangChain's <a href="https://js.langchain.com/docs/how_to/agent_executor">AgentExecutor</a> class.
    </p>
</div>

## Setup

This guide will use OpenAI's GPT-4o model. We will optionally set our API key
for [LangSmith tracing](https://smith.langchain.com/), which will give us
best-in-class observability.

---


```typescript
// process.env.OPENAI_API_KEY = "sk_...";

// Optional, add tracing in LangSmith
// process.env.LANGCHAIN_API_KEY = "ls__...";
// process.env.LANGCHAIN_CALLBACKS_BACKGROUND = "true";
// process.env.LANGCHAIN_TRACING = "true";
// process.env.LANGCHAIN_PROJECT = "Stream Tokens: LangGraphJS";
```

## Define the state

The state is the interface for all of the nodes in our graph.



```typescript
import { Annotation } from "@langchain/langgraph";
import type { BaseMessageLike } from "@langchain/core/messages";

const StateAnnotation = Annotation.Root({
  messages: Annotation<BaseMessageLike[]>({
    reducer: (x, y) => x.concat(y),
  }),
});
```

## Set up the tools

First define the tools you want to use. For this simple example, we'll create a placeholder search engine, but see the documentation [here](https://js.langchain.com/docs/how_to/custom_tools) on how to create your own custom tools.


```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const searchTool = tool((_) => {
  // This is a placeholder for the actual implementation
  return "Cold, with a low of 3℃";
}, {
  name: "search",
  description:
    "Use to surf the web, fetch current information, check the weather, and retrieve other information.",
  schema: z.object({
    query: z.string().describe("The query to use in your search."),
  }),
});

await searchTool.invoke({ query: "What's the weather like?" });

const tools = [searchTool];
```

We can now wrap these tools in a prebuilt
<a href="/langgraphjs/reference/classes/langgraph_prebuilt.ToolNode.html">ToolNode</a>.
This object will actually run the tools (functions) whenever they are invoked by
our LLM.


```typescript
import { ToolNode } from "@langchain/langgraph/prebuilt";

const toolNode = new ToolNode(tools);
```

## Set up the model

Now load the [chat model](https://js.langchain.com/docs/concepts/#chat-models).

1. It should work with messages. We will represent all agent state in the form
   of messages, so it needs to be able to work well with them.
2. It should work with
   [tool calling](https://js.langchain.com/docs/how_to/tool_calling/#passing-tools-to-llms),
   meaning it can return function arguments in its response.

<div class="admonition tip">
    <p class="admonition-title">Note</p>
    <p>
        These model requirements are not general requirements for using LangGraph - they are just requirements for this one example.
    </p>
</div>


```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  temperature: 0,
});
```

After you've done this, we should make sure the model knows that it has these
tools available to call. We can do this by calling
[bindTools](https://v01.api.js.langchain.com/classes/langchain_core_language_models_chat_models.BaseChatModel.html#bindTools).


```typescript
const boundModel = model.bindTools(tools);
```

## Define the graph

We can now put it all together.


```typescript
import { StateGraph, END } from "@langchain/langgraph";
import { AIMessage } from "@langchain/core/messages";

const routeMessage = (state: typeof StateAnnotation.State) => {
  const { messages } = state;
  const lastMessage = messages[messages.length - 1] as AIMessage;
  // If no tools are called, we can finish (respond to the user)
  if (!lastMessage?.tool_calls?.length) {
    return END;
  }
  // Otherwise if there is, we continue and call the tools
  return "tools";
};

const callModel = async (
  state: typeof StateAnnotation.State,
) => {
  // For versions of @langchain/core < 0.2.3, you must call `.stream()`
  // and aggregate the message from chunks instead of calling `.invoke()`.
  const { messages } = state;
  const responseMessage = await boundModel.invoke(messages);
  return { messages: [responseMessage] };
};

const workflow = new StateGraph(StateAnnotation)
  .addNode("agent", callModel)
  .addNode("tools", toolNode)
  .addEdge("__start__", "agent")
  .addConditionalEdges("agent", routeMessage)
  .addEdge("tools", "agent");

const agent = workflow.compile();
```


```typescript
import * as tslab from "tslab";

const runnableGraph = agent.getGraph();
const image = await runnableGraph.drawMermaidPng();
const arrayBuffer = await image.arrayBuffer();

await tslab.display.png(new Uint8Array(arrayBuffer));
```



## Streaming LLM Tokens

You can access the LLM tokens as they are produced by each node with two methods:

- The `stream` method along with `streamMode: "messages"`
- The `streamEvents` method

### The stream method

<div class="admonition tip">
    <p class="admonition-title">Compatibility</p>
    <p>
        This section requires <code>@langchain/langgraph>=0.2.20</code>. For help upgrading, see <a href="/langgraphjs/how-tos/manage-ecosystem-dependencies/">this guide</a>.
    </p>
</div>

For this method, you must be using an LLM that supports streaming as well (e.g. `new ChatOpenAI({ model: "gpt-4o-mini" })`) or call `.stream` on the internal LLM call.


```typescript
import { isAIMessageChunk } from "@langchain/core/messages";

const stream = await agent.stream(
  { messages: [{ role: "user", content: "What's the current weather in Nepal?" }] },
  { streamMode: "messages" },
);

for await (const [message, _metadata] of stream) {
  if (isAIMessageChunk(message) && message.tool_call_chunks?.length) {
    console.log(`${message.getType()} MESSAGE TOOL CALL CHUNK: ${message.tool_call_chunks[0].args}`);
  } else {
    console.log(`${message.getType()} MESSAGE CONTENT: ${message.content}`);
  }
}
```
```output
ai MESSAGE TOOL CALL CHUNK: 
ai MESSAGE TOOL CALL CHUNK: {"
ai MESSAGE TOOL CALL CHUNK: query
ai MESSAGE TOOL CALL CHUNK: ":"
ai MESSAGE TOOL CALL CHUNK: current
ai MESSAGE TOOL CALL CHUNK:  weather
ai MESSAGE TOOL CALL CHUNK:  in
ai MESSAGE TOOL CALL CHUNK:  Nepal
ai MESSAGE TOOL CALL CHUNK: "}
ai MESSAGE CONTENT: 
tool MESSAGE CONTENT: Cold, with a low of 3℃
ai MESSAGE CONTENT: 
ai MESSAGE CONTENT: The
ai MESSAGE CONTENT:  current
ai MESSAGE CONTENT:  weather
ai MESSAGE CONTENT:  in
ai MESSAGE CONTENT:  Nepal
ai MESSAGE CONTENT:  is
ai MESSAGE CONTENT:  cold
ai MESSAGE CONTENT: ,
ai MESSAGE CONTENT:  with
ai MESSAGE CONTENT:  a
ai MESSAGE CONTENT:  low
ai MESSAGE CONTENT:  temperature
ai MESSAGE CONTENT:  of
ai MESSAGE CONTENT:  
ai MESSAGE CONTENT: 3
ai MESSAGE CONTENT: ℃
ai MESSAGE CONTENT: .
ai MESSAGE CONTENT:
```
### Disabling streaming

If you wish to disable streaming for a given node or model call, you can add a `"nostream"` tag. Here's an example where we add an initial node with an LLM call that will not be streamed in the final output:


```typescript
import { RunnableLambda } from "@langchain/core/runnables";

const unstreamed = async (_: typeof StateAnnotation.State) => {
  const model = new ChatOpenAI({
    model: "gpt-4o-mini",
    temperature: 0,
  });
  const res = await model.invoke("How are you?");
  console.log("LOGGED UNSTREAMED MESSAGE", res.content);
  // Don't update the state, this is just to show a call that won't be streamed
  return {};
}

const agentWithNoStream = new StateGraph(StateAnnotation)
  .addNode("unstreamed",
    // Add a "nostream" tag to the entire node
    RunnableLambda.from(unstreamed).withConfig({
      tags: ["nostream"]
    })
  )
  .addNode("agent", callModel)
  .addNode("tools", toolNode)
  // Run the unstreamed node before the agent
  .addEdge("__start__", "unstreamed")
  .addEdge("unstreamed", "agent")
  .addConditionalEdges("agent", routeMessage)
  .addEdge("tools", "agent")
  .compile();

const stream = await agentWithNoStream.stream(
  { messages: [{ role: "user", content: "What's the current weather in Nepal?" }] },
  { streamMode: "messages" },
);

for await (const [message, _metadata] of stream) {
  if (isAIMessageChunk(message) && message.tool_call_chunks?.length) {
    console.log(`${message.getType()} MESSAGE TOOL CALL CHUNK: ${message.tool_call_chunks[0].args}`);
  } else {
    console.log(`${message.getType()} MESSAGE CONTENT: ${message.content}`);
  }
}
```
```output
LOGGED UNSTREAMED MESSAGE I'm just a computer program, so I don't have feelings, but I'm here and ready to help you! How can I assist you today?
ai MESSAGE TOOL CALL CHUNK: 
ai MESSAGE TOOL CALL CHUNK: {"
ai MESSAGE TOOL CALL CHUNK: query
ai MESSAGE TOOL CALL CHUNK: ":"
ai MESSAGE TOOL CALL CHUNK: current
ai MESSAGE TOOL CALL CHUNK:  weather
ai MESSAGE TOOL CALL CHUNK:  in
ai MESSAGE TOOL CALL CHUNK:  Nepal
ai MESSAGE TOOL CALL CHUNK: "}
ai MESSAGE CONTENT: 
tool MESSAGE CONTENT: Cold, with a low of 3℃
ai MESSAGE CONTENT: 
ai MESSAGE CONTENT: The
ai MESSAGE CONTENT:  current
ai MESSAGE CONTENT:  weather
ai MESSAGE CONTENT:  in
ai MESSAGE CONTENT:  Nepal
ai MESSAGE CONTENT:  is
ai MESSAGE CONTENT:  cold
ai MESSAGE CONTENT: ,
ai MESSAGE CONTENT:  with
ai MESSAGE CONTENT:  a
ai MESSAGE CONTENT:  low
ai MESSAGE CONTENT:  temperature
ai MESSAGE CONTENT:  of
ai MESSAGE CONTENT:  
ai MESSAGE CONTENT: 3
ai MESSAGE CONTENT: ℃
ai MESSAGE CONTENT: .
ai MESSAGE CONTENT:
```
If you removed the tag from the `"unstreamed"` node, the result of the model call within would also be in the final stream.

### The streamEvents method

You can also use the `streamEvents` method like this:


```typescript
const eventStream = agent.streamEvents(
  { messages: [{ role: "user", content: "What's the weather like today?" }] },
  { version: "v2" },
);

for await (const { event, data } of eventStream) {
  if (event === "on_chat_model_stream" && isAIMessageChunk(data.chunk)) {
    if (
      data.chunk.tool_call_chunks !== undefined &&
      data.chunk.tool_call_chunks.length > 0
    ) {
      console.log(data.chunk.tool_call_chunks);
    }
  }
}
```
```output
[
  {
    name: 'search',
    args: '',
    id: 'call_Qpd6frHt0yUYWynRbZEXF3le',
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: '{"',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: 'query',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: '":"',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: 'current',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: ' weather',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: ' today',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
[
  {
    name: undefined,
    args: '"}',
    id: undefined,
    index: 0,
    type: 'tool_call_chunk'
  }
]
```

---
how-tos/create-react-agent.ipynb
---

# How to use the prebuilt ReAct agent

# How to configure multiple streaming modes at the same time

This guide covers how to configure multiple streaming modes at the same time.

## Setup

First we need to install the packages required

```bash
npm install @langchain/langgraph @langchain/openai @langchain/core
```

Next, we need to set API keys for OpenAI (the LLM we will use)

```bash
export OPENAI_API_KEY=your-api-key
```

Optionally, we can set API key for [LangSmith tracing](https://smith.langchain.com/), which will give us best-in-class observability.

```bash
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_CALLBACKS_BACKGROUND="true"
export LANGCHAIN_API_KEY=your-api-key
```

## Define the graph

We'll be using a prebuilt ReAct agent for this guide.


```typescript
import { ChatOpenAI } from "@langchain/openai";
import { tool } from '@langchain/core/tools';
import { z } from 'zod';
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const model = new ChatOpenAI({
    model: "gpt-4o",
  });

const getWeather = tool((input) => {
  if (["sf", "san francisco", "san francisco, ca"].includes(input.location.toLowerCase())) {
    return "It's 60 degrees and foggy.";
  } else {
    return "It's 90 degrees and sunny.";
  }
}, {
  name: "get_weather",
  description: "Call to get the current weather.",
  schema: z.object({
    location: z.string().describe("Location to get the weather for."),
  })
})

const graph = createReactAgent({ llm: model, tools: [getWeather] });
```

## Stream Multiple

To get multiple types of streamed chunks, pass an array of values under the `streamMode` key in the second argument to `.stream()`:


```typescript
let inputs = { messages: [{ role: "user", content: "what's the weather in sf?" }] };

let stream = await graph.stream(inputs, {
  streamMode: ["updates", "debug"],
});

for await (const chunk of stream) {
  console.log(`Receiving new event of type: ${chunk[0]}`);
  console.log(chunk[1]);
  console.log("\n====\n");
}
```
```output
Receiving new event of type: debug
{
  type: 'task',
  timestamp: '2024-08-30T20:58:58.404Z',
  step: 1,
  payload: {
    id: '768110dd-6004-59f3-8671-6ca699cccd71',
    name: 'agent',
    input: { messages: [Array] },
    triggers: [ 'start:agent' ],
    interrupts: []
  }
}

====

Receiving new event of type: updates
{
  agent: {
    messages: [
      AIMessage {
        "id": "chatcmpl-A22zqTwumhtW8TMjQ1FxlzCEMBk0R",
        "content": "",
        "additional_kwargs": {
          "tool_calls": [
            {
              "id": "call_HAfilebE1q9E9OQHOlL3JYHP",
              "type": "function",
              "function": "[Object]"
            }
          ]
        },
        "response_metadata": {
          "tokenUsage": {
            "completionTokens": 15,
            "promptTokens": 59,
            "totalTokens": 74
          },
          "finish_reason": "tool_calls",
          "system_fingerprint": "fp_157b3831f5"
        },
        "tool_calls": [
          {
            "name": "get_weather",
            "args": {
              "location": "San Francisco"
            },
            "type": "tool_call",
            "id": "call_HAfilebE1q9E9OQHOlL3JYHP"
          }
        ],
        "invalid_tool_calls": [],
        "usage_metadata": {
          "input_tokens": 59,
          "output_tokens": 15,
          "total_tokens": 74
        }
      }
    ]
  }
}

====

Receiving new event of type: debug
{
  type: 'task_result',
  timestamp: '2024-08-30T20:58:59.072Z',
  step: 1,
  payload: {
    id: '768110dd-6004-59f3-8671-6ca699cccd71',
    name: 'agent',
    result: [ [Array] ]
  }
}

====

Receiving new event of type: debug
{
  type: 'task',
  timestamp: '2024-08-30T20:58:59.074Z',
  step: 2,
  payload: {
    id: '76459c18-5621-5893-9b93-13bc1db3ba6d',
    name: 'tools',
    input: { messages: [Array] },
    triggers: [ 'branch:agent:shouldContinue:tools' ],
    interrupts: []
  }
}

====

Receiving new event of type: updates
{
  tools: {
    messages: [
      ToolMessage {
        "content": "It's 60 degrees and foggy.",
        "name": "get_weather",
        "additional_kwargs": {},
        "response_metadata": {},
        "tool_call_id": "call_HAfilebE1q9E9OQHOlL3JYHP"
      }
    ]
  }
}

====

Receiving new event of type: debug
{
  type: 'task_result',
  timestamp: '2024-08-30T20:58:59.076Z',
  step: 2,
  payload: {
    id: '76459c18-5621-5893-9b93-13bc1db3ba6d',
    name: 'tools',
    result: [ [Array] ]
  }
}

====

Receiving new event of type: debug
{
  type: 'task',
  timestamp: '2024-08-30T20:58:59.077Z',
  step: 3,
  payload: {
    id: '565d8a53-1057-5d83-bda8-ba3fada24b70',
    name: 'agent',
    input: { messages: [Array] },
    triggers: [ 'tools' ],
    interrupts: []
  }
}

====

Receiving new event of type: updates
{
  agent: {
    messages: [
      AIMessage {
        "id": "chatcmpl-A22zrdeobsBzkiES0C6Twh3p7I344",
        "content": "The weather in San Francisco right now is 60 degrees and foggy.",
        "additional_kwargs": {},
        "response_metadata": {
          "tokenUsage": {
            "completionTokens": 16,
            "promptTokens": 90,
            "totalTokens": 106
          },
          "finish_reason": "stop",
          "system_fingerprint": "fp_157b3831f5"
        },
        "tool_calls": [],
        "invalid_tool_calls": [],
        "usage_metadata": {
          "input_tokens": 90,
          "output_tokens": 16,
          "total_tokens": 106
        }
      }
    ]
  }
}

====

Receiving new event of type: debug
{
  type: 'task_result',
  timestamp: '2024-08-30T20:58:59.640Z',
  step: 3,
  payload: {
    id: '565d8a53-1057-5d83-bda8-ba3fada24b70',
    name: 'agent',
    result: [ [Array] ]
  }
}

====
```

---
how-tos/node-retry-policies.ipynb
---



---

The MIT License

Copyright (c) 2024 LangChain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
