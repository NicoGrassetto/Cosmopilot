document.documentElement.classList.remove("no-js");

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const ANIMATION_SPEED = 0.2;
const MOTION_DURATION_SCALE = 1 / ANIMATION_SPEED;
const DECK_SLIDES = ["gateway", "pipeline", "catalog", "rank"];
const POLICY_RANK_ZONES = ["unranked", "must", "nice", "sometimes"];
const POLICY_RANK_STORAGE_KEY = "ai-gateway-policy-ranking-v1";
const SOURCE_ORDER = ["users", "agents", "mcps", "tools", "models"];
const PROVIDER_ORDER = ["foundry", "bedrock", "vertex", "local", "other"];
const STAGE_ORDER = ["ingress", "policies", "route", "response"];
const PROVIDER_LATENCY = {
	foundry: 108,
	bedrock: 154,
	vertex: 138,
	local: 54,
	other: 178
};

const AI_POLICIES = [
	{
		id: "llm-token-limit",
		name: "Token limit",
		statement: "llm-token-limit",
		type: "ai",
		section: "Inbound",
		description: "Limits LLM tokens by rate, quota, or both for each calculated consumer key.",
		href: "https://learn.microsoft.com/azure/api-management/llm-token-limit-policy"
	},
	{
		id: "llm-emit-token-metric",
		name: "Token metrics",
		statement: "llm-emit-token-metric",
		type: "ai",
		section: "Inbound",
		description: "Sends model token-consumption metrics and dimensions to Application Insights.",
		href: "https://learn.microsoft.com/azure/api-management/llm-emit-token-metric-policy"
	},
	{
		id: "llm-semantic-cache-lookup",
		name: "Semantic cache lookup",
		statement: "llm-semantic-cache-lookup",
		type: "ai",
		section: "Inbound",
		description: "Returns a cached completion when an earlier prompt is semantically similar.",
		href: "https://learn.microsoft.com/azure/api-management/llm-semantic-cache-lookup-policy"
	},
	{
		id: "llm-semantic-cache-store",
		name: "Semantic cache store",
		statement: "llm-semantic-cache-store",
		type: "ai",
		section: "Outbound",
		description: "Stores successful LLM completions in the configured semantic response cache.",
		href: "https://learn.microsoft.com/azure/api-management/llm-semantic-cache-store-policy"
	},
	{
		id: "llm-content-safety",
		name: "Content safety",
		statement: "llm-content-safety",
		type: "ai",
		section: "In + out",
		description: "Checks prompts or completions for harmful content, attacks, and blocklists.",
		href: "https://learn.microsoft.com/azure/api-management/llm-content-safety-policy"
	}
];

const CORE_POLICIES = [
	{
		id: "validate-azure-ad-token",
		name: "Validate Entra token",
		statement: "validate-azure-ad-token",
		type: "core",
		section: "Inbound",
		description: "Validates a Microsoft Entra JWT and its required claims before access.",
		href: "https://learn.microsoft.com/azure/api-management/validate-azure-ad-token-policy"
	},
	{
		id: "authentication-managed-identity",
		name: "Managed identity",
		statement: "authentication-managed-identity",
		type: "core",
		section: "Inbound",
		description: "Obtains an identity token so the gateway can call an Azure backend keylessly.",
		href: "https://learn.microsoft.com/azure/api-management/authentication-managed-identity-policy"
	},
	{
		id: "rate-limit-by-key",
		name: "Rate limit by key",
		statement: "rate-limit-by-key",
		type: "core",
		section: "Inbound",
		description: "Prevents request spikes by limiting calls for each expression-based key.",
		href: "https://learn.microsoft.com/azure/api-management/rate-limit-by-key-policy"
	},
	{
		id: "ip-filter",
		name: "IP filter",
		statement: "ip-filter",
		type: "core",
		section: "Inbound",
		description: "Allows or denies calls from configured IP addresses and address ranges.",
		href: "https://learn.microsoft.com/azure/api-management/ip-filter-policy"
	},
	{
		id: "set-backend-service",
		name: "Set backend",
		statement: "set-backend-service",
		type: "core",
		section: "Inbound",
		description: "Routes to a backend URL or managed backend pool with load balancing.",
		href: "https://learn.microsoft.com/azure/api-management/set-backend-service-policy"
	},
	{
		id: "retry",
		name: "Retry",
		statement: "retry",
		type: "core",
		section: "Flow",
		description: "Repeats enclosed policy actions until a condition succeeds or retries end.",
		href: "https://learn.microsoft.com/azure/api-management/retry-policy"
	},
	{
		id: "set-header",
		name: "Set header",
		statement: "set-header",
		type: "core",
		section: "In + out",
		description: "Adds, replaces, appends, or removes request and response headers.",
		href: "https://learn.microsoft.com/azure/api-management/set-header-policy"
	},
	{
		id: "rewrite-uri",
		name: "Rewrite URL",
		statement: "rewrite-uri",
		type: "core",
		section: "Inbound",
		description: "Transforms a public request URL into the path expected by the backend.",
		href: "https://learn.microsoft.com/azure/api-management/rewrite-uri-policy"
	},
	{
		id: "cors",
		name: "CORS",
		statement: "cors",
		type: "core",
		section: "Inbound",
		description: "Controls browser cross-origin access and handles preflight requests.",
		href: "https://learn.microsoft.com/azure/api-management/cors-policy"
	},
	{
		id: "trace",
		name: "Trace",
		statement: "trace",
		type: "core",
		section: "Any",
		description: "Adds diagnostic events to request traces, logs, and Application Insights.",
		href: "https://learn.microsoft.com/azure/api-management/trace-policy"
	}
];

const ALL_POLICIES = [...AI_POLICIES, ...CORE_POLICIES];
const policiesById = new Map(ALL_POLICIES.map((policy) => [policy.id, policy]));

const presentation = document.querySelector("#presentation");
const trafficMap = document.querySelector("#traffic-map");
const trafficLayer = document.querySelector("#traffic-layer");
const connectionLines = document.querySelector("#connection-lines");
const trafficPackets = document.querySelector("#traffic-packets");
const gatewayCard = document.querySelector("#gateway-card");
const gatewayProcessor = document.querySelector("#gateway-processor");
const sourceButtons = [...document.querySelectorAll("[data-source]")];
const providerButtons = [...document.querySelectorAll("[data-provider]")];
const policyButtons = [...document.querySelectorAll("[data-policy]")];
const traceStages = [...document.querySelectorAll("[data-stage]")];
const routeLabel = document.querySelector("#route-label");
const phaseLabel = document.querySelector("#phase-label");
const traceMessage = document.querySelector("#trace-message");
const routeCount = document.querySelector("#route-count");
const policyCount = document.querySelector("#policy-count");
const latencyValue = document.querySelector("#latency-value");
const motionToggle = document.querySelector("#motion-toggle");
const motionLabel = motionToggle.querySelector(".motion-label");
const autoRouteToggle = document.querySelector("#auto-route-toggle");
const fullscreenToggles = [...document.querySelectorAll("[data-fullscreen-toggle]")];
const liveRegion = document.querySelector("#live-region");
const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
const deckSlideElements = [...document.querySelectorAll("[data-deck-slide]")];
const deckNavigationLinks = [...document.querySelectorAll("[data-slide-target]")];
const pipelineReplay = document.querySelector("#pipeline-replay");
const policyJourney = document.querySelector("#policy-journey");
const pipelinePacket = document.querySelector("#pipeline-packet");
const pipelineStatusLabel = document.querySelector("#pipeline-status-label");
const pipelineStepCount = document.querySelector("#pipeline-step-count");
const pipelineResult = document.querySelector("#pipeline-result");
const pipelineOrigin = document.querySelector("[data-pipeline-origin]");
const pipelineStepElements = [...document.querySelectorAll("[data-pipeline-step]")];
const rankLanes = new Map([...document.querySelectorAll("[data-rank-zone]")].map((lane) => [lane.dataset.rankZone, lane]));

const sourceLabels = new Map(sourceButtons.map((button) => [button.dataset.source, button.querySelector("strong").textContent]));
const providerLabels = new Map(providerButtons.map((button) => [button.dataset.provider, button.querySelector("strong").textContent]));
const pathData = {
	sources: new Map(),
	sourceReturns: new Map(),
	providers: new Map(),
	providerReturns: new Map()
};

const state = {
	activeSlide: "gateway",
	activeSource: "users",
	activeProvider: "foundry",
	autoRoute: true,
	motionEnabled: !reducedMotionQuery.matches,
	routing: false,
	pendingRoute: false,
	pendingAnnouncement: false,
	routeTotal: 1284,
	autoTimer: null,
	layoutFrame: null,
	pipelineRunId: 0,
	pipelineAnimation: null
};

function getAnchor(element, side) {
	const elementBounds = element.getBoundingClientRect();
	const mapBounds = trafficMap.getBoundingClientRect();
	let x = elementBounds.left - mapBounds.left + elementBounds.width / 2;

	if (side === "left") {
		x = elementBounds.left - mapBounds.left - 1;
	} else if (side === "right") {
		x = elementBounds.right - mapBounds.left + 1;
	}

	return {
		x: Math.round(x * 10) / 10,
		y: Math.round((elementBounds.top - mapBounds.top + elementBounds.height / 2) * 10) / 10
	};
}

function makeCurve(from, to) {
	const distance = Math.abs(to.x - from.x);
	const direction = Math.sign(to.x - from.x) || 1;
	const handle = Math.max(34, distance * 0.48);
	const firstControl = from.x + handle * direction;
	const secondControl = to.x - handle * direction;

	return `M ${from.x} ${from.y} C ${firstControl.toFixed(1)} ${from.y}, ${secondControl.toFixed(1)} ${to.y}, ${to.x} ${to.y}`;
}

function createStreamPath(data, classes, isActive) {
	const path = document.createElementNS(SVG_NAMESPACE, "path");
	path.setAttribute("d", data);
	path.setAttribute("class", `stream-line ${classes}${isActive ? " is-active" : ""}`);
	return path;
}

function drawConnections() {
	const mapBounds = trafficMap.getBoundingClientRect();
	if (!mapBounds.width || !mapBounds.height) {
		return;
	}

	trafficLayer.setAttribute("viewBox", `0 0 ${mapBounds.width} ${mapBounds.height}`);
	connectionLines.replaceChildren();
	trafficPackets.replaceChildren();
	pathData.sources.clear();
	pathData.sourceReturns.clear();
	pathData.providers.clear();
	pathData.providerReturns.clear();

	const gatewayIngress = getAnchor(gatewayCard, "left");
	const gatewayEgress = getAnchor(gatewayCard, "right");

	for (const button of sourceButtons) {
		const sourceAnchor = getAnchor(button, "right");
		const outbound = makeCurve(sourceAnchor, gatewayIngress);
		const inbound = makeCurve(gatewayIngress, sourceAnchor);
		const sourceId = button.dataset.source;
		pathData.sources.set(sourceId, outbound);
		pathData.sourceReturns.set(sourceId, inbound);
		connectionLines.append(createStreamPath(outbound, "source-path", sourceId === state.activeSource));
	}

	for (const button of providerButtons) {
		const providerAnchor = getAnchor(button, "left");
		const outbound = makeCurve(gatewayEgress, providerAnchor);
		const inbound = makeCurve(providerAnchor, gatewayEgress);
		const providerId = button.dataset.provider;
		pathData.providers.set(providerId, outbound);
		pathData.providerReturns.set(providerId, inbound);
		connectionLines.append(createStreamPath(outbound, "provider-path", providerId === state.activeProvider));
	}
}

function scheduleConnectionLayout() {
	if (state.layoutFrame) {
		cancelAnimationFrame(state.layoutFrame);
	}

	state.layoutFrame = requestAnimationFrame(() => {
		state.layoutFrame = null;
		drawConnections();
	});
}

function updateSelectedNodes() {
	for (const button of sourceButtons) {
		const selected = button.dataset.source === state.activeSource;
		button.classList.toggle("is-selected", selected);
		button.setAttribute("aria-pressed", String(selected));
	}

	for (const button of providerButtons) {
		const selected = button.dataset.provider === state.activeProvider;
		button.classList.toggle("is-selected", selected);
		button.setAttribute("aria-pressed", String(selected));
	}

	updateRouteCopy();
	drawConnections();
}

function updateRouteCopy() {
	const source = sourceLabels.get(state.activeSource);
	const provider = providerLabels.get(state.activeProvider);
	routeLabel.textContent = `${source} → ${provider}`;
}

function updatePolicyCount() {
	const enabledPolicies = policyButtons.filter((button) => button.getAttribute("aria-pressed") === "true");
	policyCount.textContent = String(enabledPolicies.length);
	return enabledPolicies;
}

function setTraceStage(activeStage) {
	const activeIndex = STAGE_ORDER.indexOf(activeStage);

	for (const stage of traceStages) {
		const stageIndex = STAGE_ORDER.indexOf(stage.dataset.stage);
		stage.classList.toggle("is-active", stageIndex === activeIndex);
		stage.classList.toggle("is-complete", activeStage === "complete" || (activeIndex >= 0 && stageIndex < activeIndex));
	}
}

function setTrace(message, stage, phase = message) {
	traceMessage.textContent = message;
	phaseLabel.textContent = phase;
	setTraceStage(stage);
}

function wait(milliseconds) {
	const effectiveDelay = state.motionEnabled ? milliseconds * MOTION_DURATION_SCALE : Math.min(milliseconds, 55);
	return new Promise((resolve) => window.setTimeout(resolve, effectiveDelay));
}

function travelPacket(path, kind, duration = 600) {
	if (!path || !state.motionEnabled) {
		return wait(65);
	}

	return new Promise((resolve) => {
		const packet = document.createElementNS(SVG_NAMESPACE, "circle");
		const animation = document.createElementNS(SVG_NAMESPACE, "animateMotion");
		const scaledDuration = duration * MOTION_DURATION_SCALE;
		const colors = {
			request: "#52e5ff",
			route: "#f04cc3",
			response: "#8ef0bf"
		};
		let completed = false;

		packet.setAttribute("r", kind === "response" ? "4" : "4.5");
		packet.setAttribute("fill", colors[kind]);
		packet.setAttribute("class", `traffic-packet ${kind}-packet`);
		animation.setAttribute("path", path);
		animation.setAttribute("dur", `${scaledDuration}ms`);
		animation.setAttribute("begin", "indefinite");
		animation.setAttribute("fill", "freeze");
		packet.append(animation);
		trafficPackets.append(packet);

		const finish = () => {
			if (completed) {
				return;
			}
			completed = true;
			packet.remove();
			resolve();
		};

		animation.addEventListener("endEvent", finish, { once: true });
		window.setTimeout(finish, scaledDuration + 260);

		requestAnimationFrame(() => {
			try {
				animation.beginElement();
			} catch {
				finish();
			}
		});
	});
}

function clearPolicyHighlights() {
	for (const button of policyButtons) {
		button.classList.remove("is-processing");
	}
}

function calculateLatency() {
	const baseLatency = PROVIDER_LATENCY[state.activeProvider] ?? 160;
	const policyCost = updatePolicyCount().length * 4;
	const jitter = Math.floor(Math.random() * 24);
	return baseLatency + policyCost + jitter;
}

function clearAutoTimer() {
	if (state.autoTimer) {
		clearTimeout(state.autoTimer);
		state.autoTimer = null;
	}
}

function selectNextRoute() {
	const sourceIndex = SOURCE_ORDER.indexOf(state.activeSource);
	const providerIndex = PROVIDER_ORDER.indexOf(state.activeProvider);
	state.activeSource = SOURCE_ORDER[(sourceIndex + 1) % SOURCE_ORDER.length];
	state.activeProvider = PROVIDER_ORDER[(providerIndex + 1) % PROVIDER_ORDER.length];
	updateSelectedNodes();
}

function scheduleAutoRoute() {
	clearAutoTimer();
	if (state.activeSlide !== "gateway" || !state.autoRoute || !state.motionEnabled || document.hidden || state.routing) {
		return;
	}

	state.autoTimer = window.setTimeout(() => {
		selectNextRoute();
		requestRoute(false);
	}, 1150 * MOTION_DURATION_SCALE);
}

async function runRoute(announceCompletion) {
	if (state.routing) {
		state.pendingRoute = true;
		state.pendingAnnouncement ||= announceCompletion;
		return;
	}

	state.routing = true;
	clearAutoTimer();
	clearPolicyHighlights();
	gatewayProcessor.classList.add("is-processing");
	latencyValue.textContent = "—";

	const source = sourceLabels.get(state.activeSource);
	const provider = providerLabels.get(state.activeProvider);
	const requestPath = pathData.sources.get(state.activeSource);
	const providerPath = pathData.providers.get(state.activeProvider);
	const providerReturnPath = pathData.providerReturns.get(state.activeProvider);
	const sourceReturnPath = pathData.sourceReturns.get(state.activeSource);

	setTrace(`${source} request entering the gateway`, "ingress", "Receiving request");
	await travelPacket(requestPath, "request", 580);

	setTrace("Applying gateway policies", "policies", "Inspecting policy pipeline");
	const enabledPolicies = updatePolicyCount();
	if (enabledPolicies.length === 0) {
		setTrace("Policy pipeline bypassed", "policies", "No policies enforced");
		await wait(190);
	} else {
		for (const policy of enabledPolicies) {
			clearPolicyHighlights();
			policy.classList.add("is-processing");
			phaseLabel.textContent = policy.dataset.policyLabel;
			await wait(115);
		}
	}
	clearPolicyHighlights();

	setTrace(`Routing to ${provider}`, "route", `Backend selected · ${provider}`);
	await travelPacket(providerPath, "route", 620);

	setTrace(`${provider} response returning`, "response", "Response streaming");
	await travelPacket(providerReturnPath, "response", 520);
	await travelPacket(sourceReturnPath, "response", 520);

	const latency = calculateLatency();
	state.routeTotal += 1;
	routeCount.textContent = state.routeTotal.toLocaleString("en-US");
	latencyValue.textContent = String(latency);
	setTraceStage("complete");
	phaseLabel.textContent = "Route completed";
	traceMessage.textContent = `${source} ↔ ${provider} completed in ${latency} ms`;
	gatewayProcessor.classList.remove("is-processing");

	if (announceCompletion) {
		liveRegion.textContent = `${source} was routed through AI Gateway to ${provider}. ${enabledPolicies.length} policies were enforced.`;
	}

	await wait(240);
	state.routing = false;

	if (state.pendingRoute) {
		const pendingAnnouncement = state.pendingAnnouncement;
		state.pendingRoute = false;
		state.pendingAnnouncement = false;
		runRoute(pendingAnnouncement);
		return;
	}

	scheduleAutoRoute();
}

function requestRoute(announceCompletion = true) {
	if (!pathData.sources.size || !pathData.providers.size) {
		drawConnections();
	}
	runRoute(announceCompletion);
}

function setActiveSource(sourceId, announce = true) {
	if (!SOURCE_ORDER.includes(sourceId)) {
		return;
	}
	state.activeSource = sourceId;
	updateSelectedNodes();
	requestRoute(announce);
}

function setActiveProvider(providerId, announce = true) {
	if (!PROVIDER_ORDER.includes(providerId)) {
		return;
	}
	state.activeProvider = providerId;
	updateSelectedNodes();
	requestRoute(announce);
}

function renderPolicyCatalog() {
	const renderCards = (policies, container) => {
		const cards = policies.map((policy) => {
			const card = document.createElement("a");
			card.className = `catalog-card ${policy.type === "ai" ? "ai-card" : "core-card"}`;
			card.href = policy.href;
			card.target = "_blank";
			card.rel = "noreferrer";
			card.setAttribute("aria-label", `${policy.name}: ${policy.description}. Open policy reference.`);
			card.innerHTML = `
				<code>${policy.statement}</code>
				<span class="policy-section">${policy.section}</span>
				<p>${policy.description}</p>
			`;
			return card;
		});
		container.replaceChildren(...cards);
	};

	renderCards(AI_POLICIES, document.querySelector("#ai-policy-grid"));
	renderCards(CORE_POLICIES, document.querySelector("#core-policy-grid"));
}

function getJourneyPoint(element) {
	const journeyBounds = policyJourney.getBoundingClientRect();
	const elementBounds = element.getBoundingClientRect();
	return {
		x: elementBounds.left - journeyBounds.left + elementBounds.width / 2 - pipelinePacket.offsetWidth / 2,
		y: elementBounds.top - journeyBounds.top + elementBounds.height / 2 - pipelinePacket.offsetHeight / 2
	};
}

function setPipelinePacketPosition(element) {
	const point = getJourneyPoint(element);
	pipelinePacket.style.transform = `translate(${point.x}px, ${point.y}px)`;
	return point;
}

async function movePipelinePacket(fromElement, toElement, runId) {
	if (runId !== state.pipelineRunId) {
		return;
	}

	const from = getJourneyPoint(fromElement);
	const to = getJourneyPoint(toElement);
	pipelinePacket.style.opacity = "1";

	if (!state.motionEnabled || window.matchMedia("(max-width: 1100px), (max-aspect-ratio: 4 / 3)").matches) {
		pipelinePacket.style.transform = `translate(${to.x}px, ${to.y}px)`;
		await wait(65);
		return;
	}

	const animation = pipelinePacket.animate(
		[
			{ transform: `translate(${from.x}px, ${from.y}px)` },
			{ transform: `translate(${to.x}px, ${to.y}px)` }
		],
		{
			duration: 500 * MOTION_DURATION_SCALE,
			easing: "cubic-bezier(0.45, 0, 0.25, 1)",
			fill: "forwards"
		}
	);
	state.pipelineAnimation = animation;

	try {
		await animation.finished;
	} catch {
		// A replay or slide change intentionally cancels the current visual run.
	}

	if (runId !== state.pipelineRunId) {
		return;
	}

	pipelinePacket.style.transform = `translate(${to.x}px, ${to.y}px)`;
	animation.cancel();
	state.pipelineAnimation = null;
}

function resetPipelineVisuals() {
	for (const element of pipelineStepElements) {
		element.classList.remove("is-current", "is-complete");
	}
	pipelineOrigin.classList.remove("is-current");
	pipelinePacket.classList.remove("is-returning");
	pipelinePacket.style.opacity = "0";
	pipelineStepCount.textContent = "0 / 11";
	pipelineResult.textContent = "Pending";
	pipelineStatusLabel.textContent = "Ready to send a request";
}

async function runPolicyPipeline() {
	state.pipelineAnimation?.cancel();
	state.pipelineAnimation = null;
	state.pipelineRunId += 1;
	const runId = state.pipelineRunId;
	resetPipelineVisuals();

	if (state.activeSlide !== "pipeline") {
		return;
	}

	const orderedSteps = [...pipelineStepElements].sort((left, right) => Number(left.dataset.pipelineStep) - Number(right.dataset.pipelineStep));
	let previousElement = pipelineOrigin;
	pipelineOrigin.classList.add("is-current");
	setPipelinePacketPosition(pipelineOrigin);
	pipelinePacket.style.opacity = state.motionEnabled ? "1" : "0";
	await wait(100);

	for (const step of orderedSteps) {
		if (runId !== state.pipelineRunId || state.activeSlide !== "pipeline") {
			return;
		}

		pipelineOrigin.classList.remove("is-current");
		for (const element of orderedSteps) {
			element.classList.toggle("is-current", element === step);
		}

		const stepNumber = Number(step.dataset.pipelineStep);
		pipelinePacket.classList.toggle("is-returning", stepNumber >= 8);
		pipelineStatusLabel.textContent = step.dataset.status;
		pipelineResult.textContent = stepNumber === 7 ? "Backend" : step.classList.contains("ai-policy") ? "AI policy" : "API policy";
		await movePipelinePacket(previousElement, step, runId);

		if (runId !== state.pipelineRunId) {
			return;
		}

		step.classList.remove("is-current");
		step.classList.add("is-complete");
		pipelineStepCount.textContent = `${stepNumber} / 11`;
		previousElement = step;
		await wait(90);
	}

	if (runId !== state.pipelineRunId || state.activeSlide !== "pipeline") {
		return;
	}

	pipelineOrigin.classList.add("is-current");
	pipelineStatusLabel.textContent = "Governed response delivered to the application";
	await movePipelinePacket(previousElement, pipelineOrigin, runId);
	pipelinePacket.style.opacity = "0";
	pipelineOrigin.classList.remove("is-current");
	pipelineResult.textContent = "200 OK";
	liveRegion.textContent = "The request completed all eleven stages across the API and AI policy planes.";
}

let selectedRankPolicyId = null;
let draggingRankPolicyId = null;
let rankDragStarted = false;
let rankBoard = Object.fromEntries(POLICY_RANK_ZONES.map((zone) => [zone, []]));

function restoreRankBoard() {
	try {
		const storedBoard = JSON.parse(localStorage.getItem(POLICY_RANK_STORAGE_KEY));
		const restoredIds = new Set();

		for (const zone of POLICY_RANK_ZONES) {
			if (!Array.isArray(storedBoard?.[zone])) {
				continue;
			}

			for (const policyId of storedBoard[zone]) {
				if (policiesById.has(policyId) && !restoredIds.has(policyId)) {
					rankBoard[zone].push(policyId);
					restoredIds.add(policyId);
				}
			}
		}

		for (const policy of ALL_POLICIES) {
			if (!restoredIds.has(policy.id)) {
				rankBoard.unranked.push(policy.id);
			}
		}
	} catch {
		rankBoard.unranked = ALL_POLICIES.map((policy) => policy.id);
	}
}

function saveRankBoard() {
	try {
		localStorage.setItem(POLICY_RANK_STORAGE_KEY, JSON.stringify(rankBoard));
	} catch {
		liveRegion.textContent = "The ranking changed, but this browser could not save it.";
	}
}

function moveRankPolicy(policyId, destination) {
	if (!policiesById.has(policyId) || !POLICY_RANK_ZONES.includes(destination)) {
		return;
	}

	for (const zone of POLICY_RANK_ZONES) {
		rankBoard[zone] = rankBoard[zone].filter((id) => id !== policyId);
	}
	rankBoard[destination].push(policyId);
	saveRankBoard();
	renderRankBoard(policyId);
	liveRegion.textContent = `${policiesById.get(policyId).name} moved to ${destination === "unranked" ? "unranked" : destination === "must" ? "Must have" : destination === "nice" ? "Nice to have" : "Sometimes"}.`;
}

function renderRankBoard(focusPolicyId = null) {
	const scrollPositions = new Map([...rankLanes].map(([zone, lane]) => [zone, lane.scrollLeft]));

	for (const [zone, lane] of rankLanes) {
		lane.replaceChildren();

		for (const policyId of rankBoard[zone]) {
			const policy = policiesById.get(policyId);
			const card = document.createElement("button");
			card.type = "button";
			card.className = "rank-policy-card";
			card.dataset.rankPolicyId = policy.id;
			card.draggable = true;
			card.setAttribute("aria-pressed", String(selectedRankPolicyId === policy.id));
			card.setAttribute("aria-label", `${policy.name}, ${policy.type === "ai" ? "AI-specific" : "core API"} policy. ${policy.description}`);
			card.title = policy.description;
			card.innerHTML = `
				<span class="policy-kind ${policy.type}">${policy.type === "ai" ? "AI" : "API"}</span>
				<strong>${policy.name}</strong>
				<code>${policy.statement}</code>
			`;

			if (selectedRankPolicyId === policy.id) {
				card.classList.add("is-selected");
			}

			card.addEventListener("click", () => {
				if (rankDragStarted) {
					return;
				}
				selectedRankPolicyId = selectedRankPolicyId === policy.id ? null : policy.id;
				renderRankBoard(policy.id);
			});

			card.addEventListener("dragstart", (event) => {
				draggingRankPolicyId = policy.id;
				rankDragStarted = true;
				card.classList.add("is-dragging");
				event.dataTransfer.effectAllowed = "move";
				event.dataTransfer.setData("text/plain", policy.id);
			});

			card.addEventListener("dragend", () => {
				draggingRankPolicyId = null;
				card.classList.remove("is-dragging");
				document.querySelectorAll(".rank-card-lane.is-drag-over").forEach((element) => element.classList.remove("is-drag-over"));
				window.setTimeout(() => {
					rankDragStarted = false;
				}, 0);
			});

			lane.append(card);
		}

		lane.dataset.empty = String(lane.childElementCount === 0);
		lane.scrollLeft = scrollPositions.get(zone) ?? 0;
	}

	const rankedCount = ALL_POLICIES.length - rankBoard.unranked.length;
	document.querySelector("#rank-progress-label").textContent = `${rankedCount} / ${ALL_POLICIES.length} ranked`;
	document.querySelector("#rank-progress-fill").style.width = `${rankedCount / ALL_POLICIES.length * 100}%`;
	document.querySelector(".rank-progress").setAttribute("aria-valuenow", String(rankedCount));
	document.querySelector("#unranked-policy-count").textContent = String(rankBoard.unranked.length);

	if (focusPolicyId) {
		document.querySelector(`[data-rank-policy-id="${focusPolicyId}"]`)?.focus({ preventScroll: true });
	}
}

function showSlide(slideId, updateHash = false) {
	const nextSlide = DECK_SLIDES.includes(slideId) ? slideId : "gateway";
	state.pipelineAnimation?.cancel();
	state.pipelineAnimation = null;
	state.pipelineRunId += 1;
	state.activeSlide = nextSlide;
	clearAutoTimer();

	for (const slide of deckSlideElements) {
		slide.hidden = slide.dataset.deckSlide !== nextSlide;
	}
	if (nextSlide !== "pipeline") {
		resetPipelineVisuals();
	}

	for (const link of deckNavigationLinks) {
		if (link.dataset.slideTarget === nextSlide) {
			link.setAttribute("aria-current", "page");
		} else {
			link.removeAttribute("aria-current");
		}
	}

	const titles = {
		gateway: "AI Gateway — One Governed Path",
		pipeline: "AI Gateway — Policy Flow",
		catalog: "AI Gateway — Policy Catalog",
		rank: "AI Gateway — Policy Ranking"
	};
	document.title = titles[nextSlide];

	if (updateHash && window.location.hash !== `#${nextSlide}`) {
		window.location.hash = nextSlide;
	}

	if (nextSlide === "gateway") {
		requestAnimationFrame(() => {
			drawConnections();
			if (!state.routing) {
				window.setTimeout(() => requestRoute(false), state.motionEnabled ? 450 * MOTION_DURATION_SCALE : 60);
			}
		});
	} else if (nextSlide === "pipeline") {
		window.setTimeout(runPolicyPipeline, 180);
	}

	if (window.matchMedia("(max-width: 1100px), (max-aspect-ratio: 4 / 3)").matches) {
		window.scrollTo({ top: 0, behavior: "instant" });
	}
}

function syncMotionControl() {
	motionToggle.setAttribute("aria-pressed", String(state.motionEnabled));
	motionToggle.setAttribute("aria-label", state.motionEnabled ? "Pause traffic animation" : "Play traffic animation");
	motionLabel.textContent = state.motionEnabled ? "Pause" : "Play";
	trafficMap.classList.toggle("is-paused", !state.motionEnabled);

	if (state.motionEnabled) {
		try {
			trafficLayer.unpauseAnimations();
		} catch {
			// SVG animation controls are optional in some browsers.
		}
		scheduleAutoRoute();
	} else {
		clearAutoTimer();
		try {
			trafficLayer.pauseAnimations();
		} catch {
			// Static paths remain usable when SVG animation controls are unavailable.
		}
	}
}

function syncAutoRouteControl() {
	autoRouteToggle.setAttribute("aria-pressed", String(state.autoRoute));
	if (state.autoRoute) {
		scheduleAutoRoute();
	} else {
		clearAutoTimer();
	}
}

for (const button of sourceButtons) {
	button.addEventListener("click", () => setActiveSource(button.dataset.source));
}

for (const button of providerButtons) {
	button.addEventListener("click", () => setActiveProvider(button.dataset.provider));
}

for (const button of policyButtons) {
	button.addEventListener("click", () => {
		const willEnable = button.getAttribute("aria-pressed") !== "true";
		button.setAttribute("aria-pressed", String(willEnable));
		updatePolicyCount();
		liveRegion.textContent = `${button.querySelector("strong").textContent} policy ${willEnable ? "enabled" : "bypassed"}.`;
		requestRoute(false);
	});
}

motionToggle.addEventListener("click", () => {
	state.motionEnabled = !state.motionEnabled;
	syncMotionControl();
	liveRegion.textContent = `Traffic animation ${state.motionEnabled ? "playing" : "paused"}.`;
	if (state.motionEnabled && !state.routing) {
		requestRoute(false);
	}
});

autoRouteToggle.addEventListener("click", () => {
	state.autoRoute = !state.autoRoute;
	syncAutoRouteControl();
	liveRegion.textContent = `Automatic routing ${state.autoRoute ? "enabled" : "disabled"}.`;
});

pipelineReplay.addEventListener("click", runPolicyPipeline);

for (const [zone, lane] of rankLanes) {
	lane.addEventListener("dragover", (event) => {
		if (!draggingRankPolicyId) {
			return;
		}
		event.preventDefault();
		event.dataTransfer.dropEffect = "move";
		lane.classList.add("is-drag-over");
	});

	lane.addEventListener("dragleave", (event) => {
		if (!lane.contains(event.relatedTarget)) {
			lane.classList.remove("is-drag-over");
		}
	});

	lane.addEventListener("drop", (event) => {
		event.preventDefault();
		const policyId = draggingRankPolicyId || event.dataTransfer.getData("text/plain");
		lane.classList.remove("is-drag-over");
		moveRankPolicy(policyId, zone);
	});

	lane.addEventListener("click", (event) => {
		if (selectedRankPolicyId && !event.target.closest(".rank-policy-card")) {
			moveRankPolicy(selectedRankPolicyId, zone);
		}
	});

	lane.addEventListener("keydown", (event) => {
		if (selectedRankPolicyId && (event.key === "Enter" || event.key === " ")) {
			event.preventDefault();
			moveRankPolicy(selectedRankPolicyId, zone);
		}
	});
}

document.querySelectorAll("[data-rank-target]").forEach((button) => {
	button.addEventListener("click", () => {
		if (selectedRankPolicyId) {
			moveRankPolicy(selectedRankPolicyId, button.dataset.rankTarget);
		}
	});
});

document.querySelector("#rank-reset").addEventListener("click", () => {
	rankBoard = Object.fromEntries(POLICY_RANK_ZONES.map((zone) => [zone, zone === "unranked" ? ALL_POLICIES.map((policy) => policy.id) : []]));
	selectedRankPolicyId = null;
	saveRankBoard();
	renderRankBoard();
	liveRegion.textContent = "All policies returned to the unranked tray.";
});

for (const link of deckNavigationLinks) {
	link.addEventListener("click", (event) => {
		event.preventDefault();
		const slideId = link.dataset.slideTarget;
		if (window.location.hash === `#${slideId}`) {
			showSlide(slideId);
		} else {
			window.location.hash = slideId;
		}
	});
}

window.addEventListener("hashchange", () => {
	showSlide(window.location.hash.slice(1));
});

for (const fullscreenToggle of fullscreenToggles) {
	fullscreenToggle.addEventListener("click", async () => {
		try {
			if (document.fullscreenElement) {
				await document.exitFullscreen();
			} else {
				await presentation.requestFullscreen();
			}
		} catch {
			liveRegion.textContent = "Full screen is not available in this browser.";
		}
	});
}

document.addEventListener("fullscreenchange", () => {
	const isFullscreen = Boolean(document.fullscreenElement);
	for (const fullscreenToggle of fullscreenToggles) {
		fullscreenToggle.setAttribute("aria-label", isFullscreen ? "Exit full screen" : "Enter full screen");
		fullscreenToggle.title = isFullscreen ? "Exit full screen (F)" : "Full screen (F)";
	}
	scheduleConnectionLayout();
});

document.addEventListener("keydown", (event) => {
	if (event.target.closest("button, a, input, textarea, select")) {
		return;
	}

	if (event.key.toLowerCase() === "f") {
		event.preventDefault();
		fullscreenToggles[0].click();
	} else if (event.key === " " && state.activeSlide === "gateway") {
		event.preventDefault();
		motionToggle.click();
	} else if (event.key.toLowerCase() === "r") {
		event.preventDefault();
		if (state.activeSlide === "pipeline") {
			runPolicyPipeline();
		} else if (state.activeSlide === "gateway") {
			requestRoute(true);
		}
	} else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
		event.preventDefault();
		const currentIndex = DECK_SLIDES.indexOf(state.activeSlide);
		const offset = event.key === "ArrowLeft" ? -1 : 1;
		const targetIndex = Math.max(0, Math.min(DECK_SLIDES.length - 1, currentIndex + offset));
		if (targetIndex !== currentIndex) {
			window.location.hash = DECK_SLIDES[targetIndex];
		}
	}
});

document.addEventListener("visibilitychange", () => {
	if (document.hidden) {
		clearAutoTimer();
	} else {
		scheduleAutoRoute();
	}
});

reducedMotionQuery.addEventListener("change", (event) => {
	if (event.matches) {
		state.motionEnabled = false;
		syncMotionControl();
		liveRegion.textContent = "Traffic animation paused to follow the reduced motion preference.";
	}
});

window.addEventListener("resize", scheduleConnectionLayout);
window.addEventListener("load", () => {
	if (state.activeSlide === "gateway") {
		scheduleConnectionLayout();
	}
});

if (window.ResizeObserver) {
	const layoutObserver = new ResizeObserver(scheduleConnectionLayout);
	layoutObserver.observe(trafficMap);
}

updatePolicyCount();
updateSelectedNodes();
syncMotionControl();
syncAutoRouteControl();
setTraceStage(null);
renderPolicyCatalog();
restoreRankBoard();
renderRankBoard();
showSlide(window.location.hash.slice(1));
