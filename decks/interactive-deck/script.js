const TOOLS = [
	{
		id: "a2a",
		name: "Agent-to-Agent (A2A)",
		availability: "ga",
		availabilityLabel: "GA API*",
		icon: "network",
		fallback: "A2A",
		description: "Connects an agent to another agent through an A2A-compatible endpoint for delegated cross-agent work."
	},
	{
		id: "apply-patch",
		name: "Apply Patch",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "file-pen-line",
		fallback: "PT",
		description: "Lets a model propose structured file patches that a trusted client runtime reviews and applies."
	},
	{
		id: "azure-ai-search",
		name: "Azure AI Search",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "database",
		fallback: "AI",
		description: "Grounds agent responses in an existing Azure AI Search index with vector, keyword, or hybrid retrieval."
	},
	{
		id: "azure-functions",
		name: "Azure Functions",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "workflow",
		fallback: "FN",
		description: "Queues calls to Azure Functions so agents can trigger custom actions and retrieve dynamic results."
	},
	{
		id: "browser-automation",
		name: "Browser Automation",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "panel-top",
		fallback: "BR",
		description: "Runs natural-language browser tasks in a connected Playwright workspace."
	},
	{
		id: "capture-structured-outputs",
		name: "Capture Structured Outputs",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "braces",
		fallback: "SO",
		description: "Captures a named, schema-validated object from an agent run for downstream processing."
	},
	{
		id: "code-interpreter",
		name: "Code Interpreter",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "code-2",
		fallback: "CI",
		description: "Writes and runs Python in a Microsoft-managed sandbox for analysis, math, files, and charts."
	},
	{
		id: "computer",
		name: "Computer",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "monitor-cog",
		fallback: "PC",
		description: "Exposes the stable Responses computer-action primitive for runtimes that execute screen interactions."
	},
	{
		id: "computer-use",
		name: "Computer Use",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "mouse-pointer-2",
		fallback: "CU",
		description: "Lets a supported model operate a remote computer through screenshots and UI actions supplied by your application."
	},
	{
		id: "custom",
		name: "Custom",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "square-terminal",
		fallback: "CT",
		description: "Accepts unconstrained text or grammar-constrained input for a client-executed custom tool."
	},
	{
		id: "custom-code-interpreter",
		name: "Custom Code Interpreter",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "container",
		fallback: "CC",
		description: "Connects an MCP-hosted interpreter on Azure Container Apps Dynamic Sessions with custom packages and compute."
	},
	{
		id: "fabric-data-agent",
		name: "Microsoft Fabric Data Agent",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "chart-no-axes-combined",
		fallback: "FD",
		description: "Connects an agent to a published Microsoft Fabric data agent for governed data analysis."
	},
	{
		id: "fabric-iq",
		name: "Fabric IQ",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "chart-spline",
		fallback: "FI",
		description: "Queries Fabric ontologies, data agents, or Power BI semantic models through the Fabric IQ MCP endpoint."
	},
	{
		id: "file-search",
		name: "File Search",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "files",
		fallback: "FS",
		description: "Retrieves relevant passages from files ingested into a Foundry vector store."
	},
	{
		id: "function-calling",
		name: "Function Calling",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "square-function",
		fallback: "FX",
		description: "Lets a model request a JSON-schema function that your application executes and returns."
	},
	{
		id: "bing-custom-search",
		name: "Grounding with Bing Custom Search",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "scan-search",
		fallback: "BC",
		description: "Grounds responses with Bing results restricted to domains configured in a Custom Search instance."
	},
	{
		id: "bing-grounding",
		name: "Grounding with Bing Search",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "search-check",
		fallback: "BG",
		description: "Retrieves current public web results through a connected Grounding with Bing resource."
	},
	{
		id: "image-generation",
		name: "Image Generation",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "image",
		fallback: "IG",
		description: "Generates or edits images with a supported image deployment inside a Responses workflow."
	},
	{
		id: "local-shell",
		name: "Local Shell",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "terminal",
		fallback: "LS",
		description: "Emits shell commands for a client-controlled local runtime to execute in a restricted environment."
	},
	{
		id: "mcp",
		name: "Model Context Protocol (MCP)",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "unplug",
		fallback: "MC",
		description: "Connects an agent to tools exposed by a remote Model Context Protocol server."
	},
	{
		id: "memory-search",
		name: "Memory Search",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "brain-circuit",
		fallback: "MS",
		description: "Retrieves and updates user-scoped profile, summary, and procedural memories from a Foundry memory store."
	},
	{
		id: "namespace",
		name: "Namespace",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "boxes",
		fallback: "NS",
		description: "Groups related callable tools under one namespace to reduce naming collisions and tool-selection overhead."
	},
	{
		id: "openapi",
		name: "OpenAPI",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "webhook",
		fallback: "OA",
		description: "Turns operations in an OpenAPI 3.0 or 3.1 specification into callable agent tools."
	},
	{
		id: "programmatic-tool-calling",
		name: "Programmatic Tool Calling",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "code-xml",
		fallback: "PT",
		description: "Allows generated code to invoke approved tools within a programmatic execution flow."
	},
	{
		id: "reminder",
		name: "Reminder",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "clock-3",
		fallback: "RM",
		description: "Schedules a hosted agent to re-enter the same conversation at a requested future time."
	},
	{
		id: "sharepoint",
		name: "SharePoint",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "building-2",
		fallback: "SP",
		description: "Grounds responses in authorized private SharePoint content using delegated user identity."
	},
	{
		id: "shell",
		name: "Shell",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "square-terminal",
		fallback: "SH",
		description: "Runs model-requested shell commands in a managed container, referenced container, or supported local environment."
	},
	{
		id: "skills",
		name: "Skills",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "package-open",
		fallback: "SK",
		description: "Packages reusable instructions and resources that hosted agents discover through toolbox MCP resources."
	},
	{
		id: "tool-search-responses",
		name: "Tool Search (Responses)",
		availability: "ga",
		availabilityLabel: "GA API",
		icon: "list-filter",
		fallback: "TS",
		description: "Discovers deferred tool definitions at runtime so models load only the tools relevant to the request."
	},
	{
		id: "tool-search-toolbox",
		name: "Tool Search (Toolbox)",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "search-code",
		fallback: "TB",
		description: "Searches a toolbox by intent and dispatches calls without exposing every contained tool up front."
	},
	{
		id: "toolbox",
		name: "Toolbox",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "library-big",
		fallback: "TB",
		description: "Versions and bundles reusable tools behind one governed MCP endpoint for attachment to multiple agents."
	},
	{
		id: "web-search",
		name: "Web Search",
		availability: "ga",
		availabilityLabel: "GA",
		icon: "globe-2",
		fallback: "WS",
		description: "Searches the public web for current information and returns answers with inline citations."
	},
	{
		id: "web-search-preview",
		name: "Web Search (Deep Research)",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "telescope",
		fallback: "DR",
		description: "Provides high-context web retrieval for deep-research models such as o3-deep-research."
	},
	{
		id: "work-iq",
		name: "Work IQ",
		availability: "preview",
		availabilityLabel: "Preview",
		icon: "briefcase-business",
		fallback: "WI",
		description: "Grounds agents in Microsoft 365 work data while honoring the signed-in user's permissions."
	}
];

const EVALUATORS = [
	{
		id: "coherence",
		name: "Coherence",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "General",
		icon: "route",
		fallback: "CO",
		description: "Measures whether a response is logically organized, consistent, and easy to follow."
	},
	{
		id: "fluency",
		name: "Fluency",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "General",
		icon: "message-square-text",
		fallback: "FL",
		description: "Measures grammar, vocabulary, readability, and natural language quality independently of factual accuracy."
	},
	{
		id: "similarity",
		name: "Similarity",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "scan-text",
		fallback: "SI",
		description: "Uses an LLM judge to score semantic closeness between a response and ground truth."
	},
	{
		id: "f1-score",
		name: "F1 Score",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "split",
		fallback: "F1",
		description: "Calculates token-overlap precision and recall between a response and reference answer."
	},
	{
		id: "bleu",
		name: "BLEU",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "languages",
		fallback: "BL",
		description: "Measures n-gram precision against reference text, commonly for translation quality."
	},
	{
		id: "gleu",
		name: "GLEU",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "spell-check-2",
		fallback: "GL",
		description: "Balances sentence-level n-gram precision and recall using Google's BLEU variant."
	},
	{
		id: "rouge",
		name: "ROUGE",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "align-left",
		fallback: "RO",
		description: "Measures recall-oriented n-gram overlap against reference text, commonly for summarization."
	},
	{
		id: "meteor",
		name: "METEOR",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Text similarity",
		icon: "orbit",
		fallback: "ME",
		description: "Aligns response and reference tokens while considering stemming, synonyms, and word order."
	},
	{
		id: "retrieval",
		name: "Retrieval",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "RAG",
		icon: "search",
		fallback: "RE",
		description: "Uses an LLM judge to score how relevant retrieved context is to the query."
	},
	{
		id: "document-retrieval",
		name: "Document Retrieval",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "RAG",
		icon: "files",
		fallback: "DR",
		description: "Compares ranked documents with relevance labels using NDCG, fidelity, holes, and related metrics."
	},
	{
		id: "groundedness",
		name: "Groundedness",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "RAG",
		icon: "anchor",
		fallback: "GR",
		description: "Scores whether response claims are supported by the supplied context."
	},
	{
		id: "groundedness-pro",
		name: "Groundedness Pro",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "RAG",
		icon: "shield-check",
		fallback: "GP",
		description: "Uses Azure AI Content Safety for binary groundedness without a judge deployment."
	},
	{
		id: "relevance",
		name: "Relevance",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "RAG",
		icon: "crosshair",
		fallback: "RV",
		description: "Scores how directly and completely a response addresses the user's query."
	},
	{
		id: "response-completeness",
		name: "Response Completeness",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "RAG",
		icon: "list-checks",
		fallback: "RC",
		description: "Scores whether a response covers the critical information present in the ground truth."
	},
	{
		id: "hate-unfairness",
		name: "Hate and Unfairness",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "shield-alert",
		fallback: "HU",
		description: "Detects hateful, discriminatory, biased, or unfair content and reports severity."
	},
	{
		id: "sexual",
		name: "Sexual",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "shield-alert",
		fallback: "SE",
		description: "Detects sexual or explicit content and reports its risk severity."
	},
	{
		id: "violence",
		name: "Violence",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "shield-alert",
		fallback: "VI",
		description: "Detects violent or threatening content and reports its risk severity."
	},
	{
		id: "self-harm",
		name: "Self-Harm",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "heart-pulse",
		fallback: "SH",
		description: "Detects content that promotes, describes, or facilitates self-harm."
	},
	{
		id: "protected-materials",
		name: "Protected Materials",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "copyright",
		fallback: "PM",
		description: "Detects potentially copyrighted or protected text in generated output."
	},
	{
		id: "indirect-attack",
		name: "Indirect Attack (XPIA)",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "bug-off",
		fallback: "IA",
		description: "Detects whether malicious instructions embedded in retrieved content manipulated the response."
	},
	{
		id: "code-vulnerability",
		name: "Code Vulnerability",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "file-warning",
		fallback: "CV",
		description: "Detects common security weaknesses in generated code, including injection flaws."
	},
	{
		id: "ungrounded-attributes",
		name: "Ungrounded Attributes",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Risk and safety",
		icon: "user-x",
		fallback: "UA",
		description: "Detects unsupported inferences about protected personal attributes or emotional states."
	},
	{
		id: "prohibited-actions",
		name: "Prohibited Actions",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Risk and safety",
		icon: "octagon-x",
		fallback: "PA",
		description: "Detects agent behavior that violates explicitly disallowed actions or tool-use policies."
	},
	{
		id: "sensitive-data-leakage",
		name: "Sensitive Data Leakage",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Risk and safety",
		icon: "lock-keyhole-open",
		fallback: "SD",
		description: "Detects whether an agent exposes financial, identity, health, or other sensitive data."
	},
	{
		id: "task-adherence",
		name: "Task Adherence",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Agent",
		icon: "clipboard-check",
		fallback: "TA",
		description: "Checks whether an agent followed its instructions, rules, constraints, and required procedure."
	},
	{
		id: "task-completion",
		name: "Task Completion",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Agent",
		icon: "circle-check-big",
		fallback: "TC",
		description: "Checks whether an agent completed the requested task with a usable end-to-end result."
	},
	{
		id: "customer-satisfaction",
		name: "Customer Satisfaction",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Agent",
		icon: "smile",
		fallback: "CS",
		description: "Scores conversation-wide helpfulness, completeness, clarity, tone, resolution, and adaptability."
	},
	{
		id: "intent-resolution",
		name: "Intent Resolution",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Agent",
		icon: "scan-search",
		fallback: "IR",
		description: "Measures whether an agent correctly identified and addressed the user's intent."
	},
	{
		id: "task-navigation-efficiency",
		name: "Task Navigation Efficiency",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "waypoints",
		fallback: "TN",
		description: "Compares actual agent actions with an expected sequence to assess workflow efficiency."
	},
	{
		id: "tool-call-accuracy",
		name: "Tool Call Accuracy",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "wrench",
		fallback: "CA",
		description: "Scores overall tool choice, parameter correctness, relevance, and efficiency."
	},
	{
		id: "tool-selection",
		name: "Tool Selection",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "list-filter",
		fallback: "TS",
		description: "Checks whether an agent chose the correct necessary tools without redundant selections."
	},
	{
		id: "tool-input-accuracy",
		name: "Tool Input Accuracy",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "braces",
		fallback: "TI",
		description: "Validates tool arguments for grounding, type, format, completeness, and appropriateness."
	},
	{
		id: "tool-output-utilization",
		name: "Tool Output Utilization",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "between-horizontal-end",
		fallback: "TO",
		description: "Checks whether an agent interpreted and used tool results correctly."
	},
	{
		id: "tool-call-success",
		name: "Tool Call Success",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Foundry",
		category: "Agent",
		icon: "badge-check",
		fallback: "TS",
		description: "Checks whether tool executions completed without technical errors, exceptions, or timeouts."
	},
	{
		id: "quality-grader",
		name: "Quality Grader",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Agent",
		icon: "gauge",
		fallback: "QG",
		description: "Combines relevance, abstention, completeness, groundedness, and context coverage into one result."
	},
	{
		id: "rubric",
		name: "Rubric",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Rubric",
		icon: "table-properties",
		fallback: "RU",
		description: "Scores responses or conversations against custom weighted dimensions with an LLM judge."
	},
	{
		id: "model-labeler",
		name: "Model Labeler",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Azure OpenAI",
		category: "Grader",
		icon: "tags",
		fallback: "ML",
		description: "Uses an LLM and custom guidelines to classify content into predefined labels."
	},
	{
		id: "string-checker",
		name: "String Checker",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Azure OpenAI",
		category: "Grader",
		icon: "text-cursor-input",
		fallback: "SC",
		description: "Performs deterministic exact, unequal, wildcard, or case-insensitive string comparisons."
	},
	{
		id: "text-similarity-grader",
		name: "Text Similarity",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Azure OpenAI",
		category: "Grader",
		icon: "git-compare-arrows",
		fallback: "TX",
		description: "Compares text with fuzzy, BLEU, GLEU, METEOR, cosine, or ROUGE metrics."
	},
	{
		id: "model-scorer",
		name: "Model Scorer",
		availability: "ga",
		availabilityLabel: "GA",
		source: "Azure OpenAI",
		category: "Grader",
		icon: "chart-no-axes-column-increasing",
		fallback: "MS",
		description: "Uses an LLM and custom guidelines to assign a numeric score in a chosen range."
	},
	{
		id: "custom-code",
		name: "Code-Based Evaluator",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Custom",
		icon: "file-code-2",
		fallback: "CE",
		description: "Runs a sandboxed Python grade function for deterministic domain-specific scoring."
	},
	{
		id: "custom-prompt",
		name: "Prompt-Based Evaluator",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Custom",
		icon: "message-square-code",
		fallback: "PE",
		description: "Uses a custom judge prompt for ordinal, continuous, or binary scoring."
	},
	{
		id: "custom-endpoint",
		name: "Endpoint-Based Evaluator",
		availability: "preview",
		availabilityLabel: "Preview",
		source: "Foundry",
		category: "Custom",
		icon: "server-cog",
		fallback: "EE",
		description: "Delegates grading to a customer-hosted HTTP endpoint for proprietary or complex scoring."
	}
];

const ZONES = ["unranked", "A", "B", "C", "D"];
const STORAGE_KEY = "foundry-tool-tier-board-v1";
const toolsById = new Map(TOOLS.map((tool) => [tool.id, tool]));
const lanes = new Map([...document.querySelectorAll("[data-zone]")].map((lane) => [lane.dataset.zone, lane]));
const liveRegion = document.querySelector("#live-region");

let activeFilter = "all";
let searchTerm = "";
let selectedToolId = null;
let draggingToolId = null;
let dragStarted = false;

let board = Object.fromEntries(ZONES.map((zone) => [zone, []]));

try {
	const storedBoard = JSON.parse(localStorage.getItem(STORAGE_KEY));
	const restoredIds = new Set();

	for (const zone of ZONES) {
		if (!Array.isArray(storedBoard?.[zone])) {
			continue;
		}

		for (const toolId of storedBoard[zone]) {
			if (toolsById.has(toolId) && !restoredIds.has(toolId)) {
				board[zone].push(toolId);
				restoredIds.add(toolId);
			}
		}
	}

	for (const tool of TOOLS) {
		if (!restoredIds.has(tool.id)) {
			board.unranked.push(tool.id);
		}
	}
} catch {
	board.unranked = TOOLS.map((tool) => tool.id);
}

function saveBoard() {
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(board));
	} catch {
		liveRegion.textContent = "The board changed, but this browser could not save it.";
	}
}

function moveTool(toolId, destination, beforeToolId = null) {
	if (!toolsById.has(toolId) || !ZONES.includes(destination)) {
		return;
	}

	for (const zone of ZONES) {
		board[zone] = board[zone].filter((id) => id !== toolId);
	}

	const destinationOrder = board[destination];
	const insertionIndex = beforeToolId ? destinationOrder.indexOf(beforeToolId) : -1;

	if (insertionIndex >= 0) {
		destinationOrder.splice(insertionIndex, 0, toolId);
	} else {
		destinationOrder.push(toolId);
	}

	saveBoard();
	renderBoard(toolId);
	liveRegion.textContent = `${toolsById.get(toolId).name} moved to ${destination === "unranked" ? "unranked" : `tier ${destination}`}.`;
}

function renderBoard(focusToolId = null) {
	const scrollPositions = new Map([...lanes].map(([zone, lane]) => [zone, lane.scrollLeft]));
	const normalizedSearch = searchTerm.trim().toLowerCase();

	for (const [zone, lane] of lanes) {
		lane.replaceChildren();

		for (const toolId of board[zone]) {
			const tool = toolsById.get(toolId);
			const matchesFilter = activeFilter === "all" || tool.availability === activeFilter;
			const matchesSearch = !normalizedSearch || `${tool.name} ${tool.description}`.toLowerCase().includes(normalizedSearch);

			if (!matchesFilter || !matchesSearch) {
				continue;
			}

			const card = document.createElement("article");
			card.className = "tool-card";
			card.dataset.toolId = tool.id;
			card.dataset.availability = tool.availability;
			card.draggable = true;
			card.tabIndex = 0;
			card.setAttribute("role", "button");
			card.setAttribute("aria-pressed", String(selectedToolId === tool.id));
			card.setAttribute("aria-describedby", "drag-instructions");
			card.setAttribute("aria-label", `${tool.name}, ${tool.availabilityLabel}. ${tool.description}`);
			card.title = tool.description;
			card.innerHTML = `
				<div class="card-meta">
					<span class="tool-icon" aria-hidden="true">
						<i data-lucide="${tool.icon}"></i>
						<span class="icon-fallback">${tool.fallback}</span>
					</span>
					<span class="availability-badge ${tool.availability}">${tool.availabilityLabel}</span>
				</div>
				<h3>${tool.name}</h3>
				<p>${tool.description}</p>
			`;

			if (selectedToolId === tool.id) {
				card.classList.add("is-selected");
			}

			card.addEventListener("click", () => {
				if (dragStarted) {
					return;
				}

				selectedToolId = selectedToolId === tool.id ? null : tool.id;
				renderBoard(tool.id);
			});

			card.addEventListener("keydown", (event) => {
				if (event.key === "Enter" || event.key === " ") {
					event.preventDefault();
					selectedToolId = selectedToolId === tool.id ? null : tool.id;
					renderBoard(tool.id);
					return;
				}

				if (!event.altKey || !event.key.startsWith("Arrow")) {
					if ((event.key === "Backspace" || event.key === "Delete") && zone !== "unranked") {
						event.preventDefault();
						moveTool(tool.id, "unranked");
					}
					return;
				}

				event.preventDefault();
				if (event.key === "ArrowUp" || event.key === "ArrowDown") {
					const zoneIndex = ZONES.indexOf(zone);
					const offset = event.key === "ArrowUp" ? -1 : 1;
					const targetZone = ZONES[Math.max(0, Math.min(ZONES.length - 1, zoneIndex + offset))];
					moveTool(tool.id, targetZone);
					return;
				}

				const currentIndex = board[zone].indexOf(tool.id);
				const offset = event.key === "ArrowLeft" ? -1 : 1;
				const targetIndex = Math.max(0, Math.min(board[zone].length - 1, currentIndex + offset));
				if (targetIndex !== currentIndex) {
					board[zone].splice(currentIndex, 1);
					board[zone].splice(targetIndex, 0, tool.id);
					saveBoard();
					renderBoard(tool.id);
				}
			});

			card.addEventListener("dragstart", (event) => {
				draggingToolId = tool.id;
				dragStarted = true;
				card.classList.add("is-dragging");
				event.dataTransfer.effectAllowed = "move";
				event.dataTransfer.setData("text/plain", tool.id);
			});

			card.addEventListener("dragend", () => {
				draggingToolId = null;
				card.classList.remove("is-dragging");
				document.querySelectorAll(".is-drag-over, .drop-before").forEach((element) => element.classList.remove("is-drag-over", "drop-before"));
				setTimeout(() => {
					dragStarted = false;
				}, 0);
			});

			lane.append(card);
		}

		lane.dataset.empty = String(lane.childElementCount === 0);
		lane.scrollLeft = scrollPositions.get(zone) ?? 0;
	}

	const rankedCount = TOOLS.length - board.unranked.length;
	document.querySelector("#total-tools").textContent = TOOLS.length;
	document.querySelector("#unranked-count").textContent = board.unranked.length;
	document.querySelector("#progress-label").textContent = `${rankedCount} / ${TOOLS.length} ranked`;
	document.querySelector("#progress-fill").style.width = `${(rankedCount / TOOLS.length) * 100}%`;
	document.querySelector("#rank-progress").setAttribute("aria-valuemax", String(TOOLS.length));
	document.querySelector("#rank-progress").setAttribute("aria-valuenow", String(rankedCount));
	document.querySelector("#return-selected").disabled = !selectedToolId || board.unranked.includes(selectedToolId);

	if (window.lucide) {
		window.lucide.createIcons();
	}

	if (focusToolId) {
		document.querySelector(`[data-tool-id="${focusToolId}"]`)?.focus({ preventScroll: true });
	}
}

for (const [zone, lane] of lanes) {
	lane.addEventListener("dragover", (event) => {
		if (!draggingToolId) {
			return;
		}

		event.preventDefault();
		event.dataTransfer.dropEffect = "move";
		lane.classList.add("is-drag-over");
		document.querySelectorAll(".drop-before").forEach((card) => card.classList.remove("drop-before"));

		const beforeCard = [...lane.querySelectorAll(".tool-card:not(.is-dragging)")].find((card) => {
			const bounds = card.getBoundingClientRect();
			return event.clientX < bounds.left + bounds.width / 2;
		});
		beforeCard?.classList.add("drop-before");
	});

	lane.addEventListener("dragleave", (event) => {
		if (!lane.contains(event.relatedTarget)) {
			lane.classList.remove("is-drag-over");
		}
	});

	lane.addEventListener("drop", (event) => {
		event.preventDefault();
		const droppedToolId = draggingToolId || event.dataTransfer.getData("text/plain");
		const beforeToolId = lane.querySelector(".drop-before")?.dataset.toolId ?? null;
		lane.classList.remove("is-drag-over");
		moveTool(droppedToolId, zone, beforeToolId);
	});

	lane.addEventListener("click", (event) => {
		if (selectedToolId && !event.target.closest(".tool-card")) {
			moveTool(selectedToolId, zone);
		}
	});

	lane.addEventListener("keydown", (event) => {
		if (selectedToolId && (event.key === "Enter" || event.key === " ")) {
			event.preventDefault();
			moveTool(selectedToolId, zone);
		}
	});
}

document.querySelectorAll("[data-zone-target]").forEach((button) => {
	button.addEventListener("click", () => {
		if (selectedToolId) {
			moveTool(selectedToolId, button.dataset.zoneTarget);
		}
	});
});

document.querySelector("#return-selected").addEventListener("click", () => {
	if (selectedToolId) {
		moveTool(selectedToolId, "unranked");
	}
});

document.querySelector("#tool-search").addEventListener("input", (event) => {
	searchTerm = event.target.value;
	renderBoard();
});

document.querySelectorAll("[data-filter]").forEach((button) => {
	button.addEventListener("click", () => {
		activeFilter = button.dataset.filter;
		document.querySelectorAll("[data-filter]").forEach((filterButton) => {
			filterButton.setAttribute("aria-pressed", String(filterButton === button));
		});
		renderBoard();
	});
});

document.querySelector("#reset-board").addEventListener("click", () => {
	const rankedCount = TOOLS.length - board.unranked.length;
	if (rankedCount > 0 && !window.confirm("Reset all tools to the unranked tray?")) {
		return;
	}

	board = Object.fromEntries(ZONES.map((zone) => [zone, zone === "unranked" ? TOOLS.map((tool) => tool.id) : []]));
	selectedToolId = null;
	saveBoard();
	renderBoard();
	liveRegion.textContent = "The tier board was reset.";
});

renderBoard();

const EVALUATION_STORAGE_KEY = "foundry-evaluation-tier-board-v1";
const evaluatorsById = new Map(EVALUATORS.map((evaluator) => [evaluator.id, evaluator]));
const evaluationLanes = new Map([...document.querySelectorAll("[data-evaluation-zone]")].map((lane) => [lane.dataset.evaluationZone, lane]));

let evaluationFilter = "all";
let evaluationSearchTerm = "";
let selectedEvaluatorId = null;
let draggingEvaluatorId = null;
let evaluationDragStarted = false;
let evaluationBoard = Object.fromEntries(ZONES.map((zone) => [zone, []]));

try {
	const storedEvaluationBoard = JSON.parse(localStorage.getItem(EVALUATION_STORAGE_KEY));
	const restoredEvaluatorIds = new Set();

	for (const zone of ZONES) {
		if (!Array.isArray(storedEvaluationBoard?.[zone])) {
			continue;
		}

		for (const evaluatorId of storedEvaluationBoard[zone]) {
			if (evaluatorsById.has(evaluatorId) && !restoredEvaluatorIds.has(evaluatorId)) {
				evaluationBoard[zone].push(evaluatorId);
				restoredEvaluatorIds.add(evaluatorId);
			}
		}
	}

	for (const evaluator of EVALUATORS) {
		if (!restoredEvaluatorIds.has(evaluator.id)) {
			evaluationBoard.unranked.push(evaluator.id);
		}
	}
} catch {
	evaluationBoard.unranked = EVALUATORS.map((evaluator) => evaluator.id);
}

function saveEvaluationBoard() {
	try {
		localStorage.setItem(EVALUATION_STORAGE_KEY, JSON.stringify(evaluationBoard));
	} catch {
		liveRegion.textContent = "The evaluation board changed, but this browser could not save it.";
	}
}

function moveEvaluator(evaluatorId, destination, beforeEvaluatorId = null) {
	if (!evaluatorsById.has(evaluatorId) || !ZONES.includes(destination)) {
		return;
	}

	for (const zone of ZONES) {
		evaluationBoard[zone] = evaluationBoard[zone].filter((id) => id !== evaluatorId);
	}

	const destinationOrder = evaluationBoard[destination];
	const insertionIndex = beforeEvaluatorId ? destinationOrder.indexOf(beforeEvaluatorId) : -1;

	if (insertionIndex >= 0) {
		destinationOrder.splice(insertionIndex, 0, evaluatorId);
	} else {
		destinationOrder.push(evaluatorId);
	}

	saveEvaluationBoard();
	renderEvaluationBoard(evaluatorId);
	liveRegion.textContent = `${evaluatorsById.get(evaluatorId).name} moved to ${destination === "unranked" ? "unranked" : `tier ${destination}`}.`;
}

function renderEvaluationBoard(focusEvaluatorId = null) {
	const scrollPositions = new Map([...evaluationLanes].map(([zone, lane]) => [zone, lane.scrollLeft]));
	const normalizedSearch = evaluationSearchTerm.trim().toLowerCase();

	for (const [zone, lane] of evaluationLanes) {
		lane.replaceChildren();

		for (const evaluatorId of evaluationBoard[zone]) {
			const evaluator = evaluatorsById.get(evaluatorId);
			const matchesFilter = evaluationFilter === "all" || evaluator.availability === evaluationFilter;
			const searchableText = `${evaluator.name} ${evaluator.description} ${evaluator.source} ${evaluator.category}`.toLowerCase();
			const matchesSearch = !normalizedSearch || searchableText.includes(normalizedSearch);

			if (!matchesFilter || !matchesSearch) {
				continue;
			}

			const card = document.createElement("article");
			card.className = "tool-card evaluator-card";
			card.dataset.evaluatorId = evaluator.id;
			card.dataset.availability = evaluator.availability;
			card.draggable = true;
			card.tabIndex = 0;
			card.setAttribute("role", "button");
			card.setAttribute("aria-pressed", String(selectedEvaluatorId === evaluator.id));
			card.setAttribute("aria-describedby", "drag-instructions");
			card.setAttribute("aria-label", `${evaluator.name}, ${evaluator.availabilityLabel}, ${evaluator.source} ${evaluator.category}. ${evaluator.description}`);
			card.title = evaluator.description;
			card.innerHTML = `
				<div class="card-meta">
					<span class="tool-icon" aria-hidden="true">
						<i data-lucide="${evaluator.icon}"></i>
						<span class="icon-fallback">${evaluator.fallback}</span>
					</span>
					<span class="availability-badge ${evaluator.availability}">${evaluator.availabilityLabel}</span>
				</div>
				<h3>${evaluator.name}</h3>
				<span class="card-source ${evaluator.source === "Azure OpenAI" ? "azure-openai" : ""}">${evaluator.source} / ${evaluator.category}</span>
				<p>${evaluator.description}</p>
			`;

			if (selectedEvaluatorId === evaluator.id) {
				card.classList.add("is-selected");
			}

			card.addEventListener("click", () => {
				if (evaluationDragStarted) {
					return;
				}

				selectedEvaluatorId = selectedEvaluatorId === evaluator.id ? null : evaluator.id;
				renderEvaluationBoard(evaluator.id);
			});

			card.addEventListener("keydown", (event) => {
				if (event.key === "Enter" || event.key === " ") {
					event.preventDefault();
					selectedEvaluatorId = selectedEvaluatorId === evaluator.id ? null : evaluator.id;
					renderEvaluationBoard(evaluator.id);
					return;
				}

				if (!event.altKey || !event.key.startsWith("Arrow")) {
					if ((event.key === "Backspace" || event.key === "Delete") && zone !== "unranked") {
						event.preventDefault();
						moveEvaluator(evaluator.id, "unranked");
					}
					return;
				}

				event.preventDefault();
				if (event.key === "ArrowUp" || event.key === "ArrowDown") {
					const zoneIndex = ZONES.indexOf(zone);
					const offset = event.key === "ArrowUp" ? -1 : 1;
					const targetZone = ZONES[Math.max(0, Math.min(ZONES.length - 1, zoneIndex + offset))];
					moveEvaluator(evaluator.id, targetZone);
					return;
				}

				const currentIndex = evaluationBoard[zone].indexOf(evaluator.id);
				const offset = event.key === "ArrowLeft" ? -1 : 1;
				const targetIndex = Math.max(0, Math.min(evaluationBoard[zone].length - 1, currentIndex + offset));
				if (targetIndex !== currentIndex) {
					evaluationBoard[zone].splice(currentIndex, 1);
					evaluationBoard[zone].splice(targetIndex, 0, evaluator.id);
					saveEvaluationBoard();
					renderEvaluationBoard(evaluator.id);
				}
			});

			card.addEventListener("dragstart", (event) => {
				draggingEvaluatorId = evaluator.id;
				evaluationDragStarted = true;
				card.classList.add("is-dragging");
				event.dataTransfer.effectAllowed = "move";
				event.dataTransfer.setData("text/plain", evaluator.id);
			});

			card.addEventListener("dragend", () => {
				draggingEvaluatorId = null;
				card.classList.remove("is-dragging");
				document.querySelectorAll(".evaluation-slide .is-drag-over, .evaluation-slide .drop-before").forEach((element) => element.classList.remove("is-drag-over", "drop-before"));
				setTimeout(() => {
					evaluationDragStarted = false;
				}, 0);
			});

			lane.append(card);
		}

		lane.dataset.empty = String(lane.childElementCount === 0);
		lane.scrollLeft = scrollPositions.get(zone) ?? 0;
	}

	const rankedCount = EVALUATORS.length - evaluationBoard.unranked.length;
	document.querySelector("#evaluation-total").textContent = EVALUATORS.length;
	document.querySelector("#evaluation-unranked-count").textContent = evaluationBoard.unranked.length;
	document.querySelector("#evaluation-progress-label").textContent = `${rankedCount} / ${EVALUATORS.length} ranked`;
	document.querySelector("#evaluation-progress-fill").style.width = `${(rankedCount / EVALUATORS.length) * 100}%`;
	document.querySelector("#evaluation-rank-progress").setAttribute("aria-valuemax", String(EVALUATORS.length));
	document.querySelector("#evaluation-rank-progress").setAttribute("aria-valuenow", String(rankedCount));
	document.querySelector("#evaluation-return-selected").disabled = !selectedEvaluatorId || evaluationBoard.unranked.includes(selectedEvaluatorId);

	if (window.lucide) {
		window.lucide.createIcons();
	}

	if (focusEvaluatorId) {
		document.querySelector(`[data-evaluator-id="${focusEvaluatorId}"]`)?.focus({ preventScroll: true });
	}
}

for (const [zone, lane] of evaluationLanes) {
	lane.addEventListener("dragover", (event) => {
		if (!draggingEvaluatorId) {
			return;
		}

		event.preventDefault();
		event.dataTransfer.dropEffect = "move";
		lane.classList.add("is-drag-over");
		document.querySelectorAll(".evaluation-slide .drop-before").forEach((card) => card.classList.remove("drop-before"));

		const beforeCard = [...lane.querySelectorAll(".evaluator-card:not(.is-dragging)")].find((card) => {
			const bounds = card.getBoundingClientRect();
			return event.clientX < bounds.left + bounds.width / 2;
		});
		beforeCard?.classList.add("drop-before");
	});

	lane.addEventListener("dragleave", (event) => {
		if (!lane.contains(event.relatedTarget)) {
			lane.classList.remove("is-drag-over");
		}
	});

	lane.addEventListener("drop", (event) => {
		event.preventDefault();
		const droppedEvaluatorId = draggingEvaluatorId || event.dataTransfer.getData("text/plain");
		const beforeEvaluatorId = lane.querySelector(".drop-before")?.dataset.evaluatorId ?? null;
		lane.classList.remove("is-drag-over");
		moveEvaluator(droppedEvaluatorId, zone, beforeEvaluatorId);
	});

	lane.addEventListener("click", (event) => {
		if (selectedEvaluatorId && !event.target.closest(".evaluator-card")) {
			moveEvaluator(selectedEvaluatorId, zone);
		}
	});

	lane.addEventListener("keydown", (event) => {
		if (selectedEvaluatorId && (event.key === "Enter" || event.key === " ")) {
			event.preventDefault();
			moveEvaluator(selectedEvaluatorId, zone);
		}
	});
}

document.querySelectorAll("[data-evaluation-zone-target]").forEach((button) => {
	button.addEventListener("click", () => {
		if (selectedEvaluatorId) {
			moveEvaluator(selectedEvaluatorId, button.dataset.evaluationZoneTarget);
		}
	});
});

document.querySelector("#evaluation-return-selected").addEventListener("click", () => {
	if (selectedEvaluatorId) {
		moveEvaluator(selectedEvaluatorId, "unranked");
	}
});

document.querySelector("#evaluation-search").addEventListener("input", (event) => {
	evaluationSearchTerm = event.target.value;
	renderEvaluationBoard();
});

document.querySelectorAll("[data-evaluation-filter]").forEach((button) => {
	button.addEventListener("click", () => {
		evaluationFilter = button.dataset.evaluationFilter;
		document.querySelectorAll("[data-evaluation-filter]").forEach((filterButton) => {
			filterButton.setAttribute("aria-pressed", String(filterButton === button));
		});
		renderEvaluationBoard();
	});
});

document.querySelector("#evaluation-reset").addEventListener("click", () => {
	const rankedCount = EVALUATORS.length - evaluationBoard.unranked.length;
	if (rankedCount > 0 && !window.confirm("Reset all evaluators to the unranked tray?")) {
		return;
	}

	evaluationBoard = Object.fromEntries(ZONES.map((zone) => [zone, zone === "unranked" ? EVALUATORS.map((evaluator) => evaluator.id) : []]));
	selectedEvaluatorId = null;
	saveEvaluationBoard();
	renderEvaluationBoard();
	liveRegion.textContent = "The evaluation tier board was reset.";
});

function showSlide(slideId, scrollToTop = true) {
	const activeSlideId = slideId === "evaluations" ? "evaluations" : "tools";

	document.querySelectorAll("[data-slide]").forEach((slide) => {
		slide.hidden = slide.dataset.slide !== activeSlideId;
	});

	document.querySelectorAll("[data-slide-link]").forEach((link) => {
		if (link.dataset.slideLink === activeSlideId) {
			link.setAttribute("aria-current", "page");
		} else {
			link.removeAttribute("aria-current");
		}
	});

	document.title = activeSlideId === "evaluations" ? "Microsoft Foundry Evaluation Tier Board" : "Microsoft Foundry Tool Tier Board";
	if (scrollToTop) {
		window.scrollTo({ top: 0, behavior: "instant" });
	}
}

document.querySelectorAll("[data-slide-link]").forEach((link) => {
	link.addEventListener("click", (event) => {
		event.preventDefault();
		const slideId = link.dataset.slideLink;
		if (window.location.hash !== `#${slideId}`) {
			window.location.hash = slideId;
		} else {
			showSlide(slideId);
		}
	});
});

window.addEventListener("hashchange", () => {
	showSlide(window.location.hash.slice(1));
});

renderEvaluationBoard();
showSlide(window.location.hash.slice(1), false);