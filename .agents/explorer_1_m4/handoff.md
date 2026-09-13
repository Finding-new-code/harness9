# Milestone 4 Technical Exploration Report: Provider & Model Routing Architecture (R4.1)

**Agent ID:** `explorer_1_m4`  
**Date:** 2026-09-05  
**Scope:** Milestone 4 (R4.1: Provider, Memory & Subagent Integration — Provider & Model Routing)  
**Status:** Completed Exploration & Architecture Specification  

---

## 1. Observation

Direct evidence gathered across the Hermes Agent core, provider registry, configuration loaders, H9 domain modules, and runtime boundary packages:

### 1.1 Hermes Provider System & Routing Architecture

1. **Provider Profiles & Base Contract (`providers/base.py`)**:
   - `ProviderProfile` is a declarative dataclass (`lines 38-102`) defining:
     * Identity: `name`, `api_mode` (default `"chat_completions"`), `aliases`.
     * Metadata: `display_name`, `description`, `signup_url`.
     * Auth & Endpoints: `env_vars`, `base_url`, `models_url`, `auth_type` (e.g. `api_key`, `oauth_device_code`, `copilot`, `aws_sdk`), `supports_health_check`.
     * Model Catalog & Quirks: `fallback_models`, `hostname`, `default_headers`, `fixed_temperature`, `default_max_tokens`, `default_aux_model`.
     * Overrideable hooks (`lines 104-297`): `resolve_aux_model()`, `prepare_messages()`, `build_extra_body()`, `build_api_kwargs_extras()`, `default_vision_model()`, `get_max_tokens()`, `supported_reasoning_efforts()`, `fetch_models()`.
   - Quote (`providers/base.py:7-9`):
     ```python
     # Provider profiles are DECLARATIVE — they describe the provider's behavior.
     # They do NOT own client construction, credential rotation, or streaming.
     # Those stay on AIAgent.
     ```

2. **Provider Plugin Discovery & Precedence (`providers/__init__.py`)**:
   - Discovers provider profiles lazily via `_discover_providers()` (`lines 271-343`):
     * Step 0: Pip-installed entry points (`hermes_agent.plugins` group via `_discover_entry_point_providers()`, lines 149-246).
     * Step 1: Bundled plugins at `<repo>/plugins/model-providers/<name>/` (`lines 303-309`).
     * Step 2: User plugins at `$HERMES_HOME/plugins/model-providers/<name>/` (`lines 310-318`).
     * Step 3: Legacy modules at `providers/<name>.py` (`lines 320-338`).
   - Discovery order enforces that user plugins override bundled plugins via **last-writer-wins** in `register_provider(profile)` (`lines 56-68`), while bundled/user plugins override pip-installed plugins.
   - 39 bundled provider plugins exist in `plugins/model-providers/`, including `anthropic`, `openrouter`, `deepseek`, `gemini`, `xai`, `bedrock`, `azure-foundry`, `gmi`, `nous`, etc.

3. **Provider Resolution & Credential Loading (`hermes_cli/runtime_provider.py`)**:
   - `resolve_runtime_provider(...)` (`lines 1876-1930`):
     * Resolves requested provider against `load_config()`.
     * Enforces `providers.<name>.enabled: false` check (`lines 1905-1915`).
     * Resolves credentials via `agent.secret_scope.get_secret()` (`lines 76-86`) protecting profile scopes in multiplexed gateways.
     * Integrates with `CredentialPool` (`agent/credential_pool.py`) for automatic multi-key rotation upon rate limits.
     * Returns dictionary containing `provider`, `api_mode`, `base_url`, `api_key`, `credential_pool`, `extra_headers`.

4. **Fallback Chains & Recovery (`hermes_cli/fallback_config.py` & `agent/agent_init.py`)**:
   - `get_fallback_chain(config)` (`hermes_cli/fallback_config.py:80-102`): Merges modern `fallback_providers` (list of provider/model dicts) and legacy `fallback_model`.
   - `agent/agent_init.py` (`lines 1570-1586`): Initializes `agent._fallback_chain` as an ordered list of fallback providers.
   - `run_agent.py` (`lines 320-343`) & `agent/conversation_loop.py`: When a rate-limit (HTTP 429) or overload occurs and the credential pool cannot rotate (e.g. single-key pool), triggers activation of the next fallback provider in `_fallback_chain`.

5. **Shared Auxiliary Router (`agent/auxiliary_client.py`)**:
   - Dedicated side-task execution engine with automatic fallback and routing (`lines 1-45`).
   - Function `call_llm(...)` (`lines 9691-9771`) and `_call_llm_impl(...)` (`lines 9796-9920`):
     * Takes task name: `call_llm(task="...", provider=..., model=..., messages=..., temperature=..., max_tokens=..., schema=...)`.
     * `_resolve_task_provider_model(task, ...)` (`lines 8311-8360`): Looks up `auxiliary.{task}.provider`, `auxiliary.{task}.model`, `auxiliary.{task}.base_url`, and `auxiliary.{task}.api_key` in `config.yaml`.
     * Automatically falls back to user's main provider/model, then OpenRouter, Nous Portal, custom base URL, native Anthropic, and direct API key providers.
     * Concurrency guarded by task-specific semaphores (`_acquire_sync_aux_semaphore`, `line 9715`).
     * Automatic credit exhaustion (HTTP 402) retry/fallback (`lines 40-44`).

---

### 1.2 H9 Model Call Sites Audit

Inspection of all H9 domain subpackages reveals that H9 currently does **NOT** make direct LLM completion calls, but instead relies on deterministic heuristics and templates:

1. **`src/editorial/` (Editorial Intelligence)**:
   - `angle_generator.py` (`lines 106-213`): `_build_angle_for_archetype()` constructs candidate angles for the 5 archetypes (`contrarian`, `deep_dive`, `data_led`, `human_narrative`, `future_impact`) using Python f-string templates. No LLM invocation is currently performed.
   - `hook_generator.py` (`lines 37-125`): `generate_hooks()` constructs 5 hook variations (`question`, `paradox`, `dramatic_statement`, `cold_open`, `statistic_shock`) via hardcoded string interpolation.
   - `narrative_planner.py` (`lines 26-119`): `build_outline()` deterministically assigns dossier talking points into 4 acts (`Hook & Paradox`, `Bottleneck & Context`, `Core Insight & Mechanism`, `Payoff & Horizon`).
   - `scorecard.py` (`lines 72-376`): `EditorialScorer.score_angle()` calculates scores across 9 dimensions using regex and heuristic word matches.

2. **`src/research/` (Research Engine)**:
   - `engine.py` (`lines 106-250`): `_synthesize_live()` queries search providers via `MultiProviderDispatcher`, splits text snippets using regex (`re.split(r"(?<=[.!?])\s+", res.snippet)`), filters sentences by character length (40 to 280), scores claims with heuristic formula (`src/research/scoring.py:score_claim`), and assembles a `ResearchDossier` without any LLM synthesis.
   - `presets/`: Curated YAML benchmarks used for offline reproducibility.

3. **`src/scriptwriting/` (Scriptwriting & Voice)**:
   - `generator.py` (`lines 351-420`): `synthesize_scenes_from_dossier()` formats scene titles, narration text, and visual cues using string concatenation.
   - `voice_director.py` (`lines 333-412`):
     * **Hardcoded Direct SDK / API Call Site**: `OpenAIAudioProvider` makes a direct HTTP POST call using Python's `urllib.request` to `https://api.openai.com/v1/audio/speech` using raw `OPENAI_API_KEY`:
       ```python
       # voice_director.py:375-385
       url = "https://api.openai.com/v1/audio/speech"
       headers = {
           "Authorization": f"Bearer {self.api_key}",
           "Content-Type": "application/json",
       }
       ```
     * Bypasses Hermes credential pooling, secret scoping, and provider abstraction.
   - `voice_qa.py` (`lines 54-100`): Pure PCM audio byte analysis (RMS loudness, peak saturation, silence frames).

4. **`src/evaluation/` (ContentBench Quality OS)**:
   - `contentbench.py` (`lines 36-100`): 4-layer evaluation calculated entirely using mathematical formulas (Flesch-Kincaid, WPM, acoustic ratios, cost ledger sums).

---

### 1.3 Runtime Boundary Interface Inspection

1. **`src/h9_runtime/models.py`**:
   - `ModelRuntime` protocol (`lines 22-57`):
     ```python
     @runtime_checkable
     class ModelRuntime(Protocol):
         def invoke_capability(self, role: CapabilityRole, prompt: str,
                               system_instruction: Optional[str] = None,
                               schema: Optional[Type[T]] = None,
                               temperature: float = 0.7,
                               max_tokens: Optional[int] = None,
                               session_id: Optional[str] = None) -> ModelResponse: ...
         def stream_capability(...) -> Iterator[str]: ...
         def estimate_tokens(self, text: str) -> int: ...
         def get_budget_status(self, session_id: str) -> BudgetStatus: ...
     ```
   - `DefaultModelRuntime` (`lines 59-236`):
     * Defines `DEFAULT_ROLE_CONFIGS` (`lines 63-84`) mapping `CapabilityRole` to model names, providers, and costs:
       - `FAST_EDITORIAL`: `claude-3-5-haiku` (`anthropic`), $0.001 / 1k tokens.
       - `REASONING_RESEARCH`: `deepseek-r1` (`openrouter`), $0.002 / 1k tokens.
       - `CREATIVE_SCRIPT`: `claude-3-5-sonnet` (`anthropic`), $0.003 / 1k tokens.
       - `ACOUSTIC_EVAL`: `acoustic-evaluator` (`hermes_auxiliary`), $0.001 / 1k tokens.
     * `invoke_capability(...)` (`lines 148-215`): Currently fills Pydantic schemas with dummy string/int sample values (`lines 176-191`) or generates stub text `"Synthesized response for [{role.value}] on prompt: ..."`.
     * Tracks token spend and cost in `_budgets[session_id]` (`lines 112-146`).

2. **`src/h9_runtime/bridge.py`**:
   - `HermesCapabilityBridge` (`lines 85-800`):
     * Central gateway conforming to all 7 runtime protocols (`AgentRuntime`, `SkillRuntime`, `ToolRuntime`, `ModelRuntime`, `MemoryRuntime`, `ExecutionRuntime`, `ContentRuntime`).
     * Exposes high-level domain helper:
       ```python
       # bridge.py:554-572
       def request_model_completion(
           self,
           role: Union[str, CapabilityRole],
           prompt: str,
           system_prompt: Optional[str] = None,
           temperature: float = 0.7,
           schema: Optional[Type[BaseModel]] = None,
       ) -> str:
           response = self.invoke_capability(
               role=role,
               prompt=prompt,
               system_instruction=system_prompt,
               schema=schema,
               temperature=temperature,
               session_id=self.session_id,
           )
           return response.content
       ```
     * Singleton accessor `get_capability_bridge(session_id)` (`lines 809-818`).

---

## 2. Logic Chain

1. **Preserving Sacred Prompt Caching & Rung 3 Service Gating**:
   - Hermes conversation turns are strictly cache-sensitive: mutating system prompts or dynamic mid-turn tool registration breaks prefix caching and multiplies costs (`AGENTS.md`).
   - Therefore, model execution requested by H9 domain logic (e.g. angle generation, research synthesis, scriptwriting) must NOT occur by injecting synthetic user turns into the parent `AIAgent` conversation loop.
   - Instead, H9 model requests must execute as **out-of-band auxiliary capability calls** via `ModelRuntime` / `HermesCapabilityBridge`, using Hermes's auxiliary client router (`agent/auxiliary_client.py:call_llm`).

2. **Eliminating Direct Vendor Client Instantiations**:
   - `voice_director.py:OpenAIAudioProvider` makes an un-gated HTTP POST call to `https://api.openai.com/v1/audio/speech`. This violates the principle of zero hardcoded vendor backends.
   - H9 domain modules must never instantiate `openai.OpenAI()`, `anthropic.Anthropic()`, or direct vendor HTTP clients.
   - All text generation must route through `ModelRuntime.invoke_capability(role, ...)`, and voice synthesis credentials must resolve through `agent.secret_scope.get_secret()` or Hermes TTS provider registry (`agent/tts_registry.py`).

3. **Bridging `ModelRuntime` to the Hermes Provider System**:
   - `DefaultModelRuntime` currently returns synthetic dummy data.
   - In Milestone 4, `DefaultModelRuntime` should bridge to Hermes's `agent/auxiliary_client.py:call_llm()`, passing `task=role.value`.
   - This provides:
     * Automatic configuration via `~/.hermes/config.yaml` under `auxiliary.<role_name>` (e.g. `auxiliary.fast_editorial.provider: anthropic`).
     * Automatic fallback through the Hermes fallback chain (`hermes_cli/fallback_config.py`).
     * Automatic handling of credit exhaustion (HTTP 402 retry on next provider).
     * Token accounting via response usage objects (`response.usage.prompt_tokens`, `response.usage.completion_tokens`).
     * Offline graceful fallback: when offline mode is active or no API credentials are configured, fallback to deterministic template generators and heuristic scorecards, preserving 100% test suite reproducibility.

4. **Designing the Concrete Mapping for Logical Capability Roles**:
   - Each role represents a distinct operational tier with differing latency, reasoning, cost, and sampling requirements.

---

## 3. Concrete Design: Logical Capability Roles Architecture

### 3.1 Role Specification Matrix

| Logical Role | Canonical Identifier | Primary Production Duties | Recommended Default Models | Temperature & Sampling Profile | Cost Tier & Constraints |
|---|---|---|---|---|---|
| **Fast Editorial** | `CapabilityRole.FAST_EDITORIAL` (`fast_editorial`) | Rapid angle generation across 5 archetypes, 9-dimension scorecard evaluation, candidate ranking, psychological hook ideation, metadata extraction. | Primary: `claude-3-5-haiku`<br>Secondary: `gpt-4o-mini`<br>Fallback: `deepseek-chat` / `qwen-2.5-72b` | `temperature: 0.35`<br>`top_p: 0.90`<br>`max_tokens: 1500`<br>Low latency (<1.5s), strict JSON adherence. | Economy (~$0.0008 - $0.001 / 1k tokens).<br>High throughput, deterministic scoring. |
| **Reasoning Research** | `CapabilityRole.REASONING_RESEARCH` (`reasoning_research`) | Multi-source research synthesis, claim extraction, conflict resolution between contradictory facts, source reliability weighting, statistical verification. | Primary: `deepseek-r1`<br>Secondary: `o3-mini`<br>Fallback: `claude-3-7-sonnet` (thinking) | `temperature: 0.60`<br>`reasoning_effort: "medium"`<br>`max_tokens: 6000`<br>Chain-of-thought verification. | Standard (~$0.002 - $0.005 / 1k tokens).<br>Zero hallucination, high analytical rigor. |
| **Creative Script** | `CapabilityRole.CREATIVE_SCRIPT` (`creative_script`) | 4-act narrative blueprinting, timestamped scene & beat composition, Creator DNA brand tone emulation, cinematic visual cue prompts, GSAP entrance animation scripting. | Primary: `claude-3-5-sonnet`<br>Secondary: `gpt-4o`<br>Fallback: `deepseek-v3` / `mistral-large` | `temperature: 0.75`<br>`top_p: 0.95`<br>`max_tokens: 3500`<br>Fluid phrasing, expressive pacing. | Premium (~$0.003 - $0.015 / 1k tokens).<br>Creator voice fidelity, temporal pacing. |
| **Acoustic Eval** | `CapabilityRole.ACOUSTIC_EVAL` (`acoustic_eval`) | Interpreting VoiceQA acoustic metrics, diagnosing dead air clusters, prosody & inflection guidance, speech-beat sync drift remediation. | Primary: `claude-3-5-haiku`<br>Secondary: `gpt-4o-mini`<br>Fallback: `auto` | `temperature: 0.15`<br>`top_p: 0.85`<br>`max_tokens: 1000`<br>Analytical diagnosis, structured feedback. | Economy (~$0.0005 - $0.001 / 1k tokens).<br>Diagnostic consistency. |

---

### 3.2 User Configuration Schema (`~/.hermes/config.yaml`)

Users configure role routing in their standard Hermes `config.yaml` using the established `auxiliary:` section. Zero new core environment variables are required:

```yaml
# ~/.hermes/config.yaml
model:
  default: claude-3-5-sonnet-20241022
  provider: anthropic

# Role-based auxiliary routing for Harness 9 content production
auxiliary:
  # R4.1: Fast Editorial Intelligence & Scorecards
  fast_editorial:
    provider: anthropic
    model: claude-3-5-haiku-20241022
    temperature: 0.35
    max_tokens: 1500

  # R4.1: Deep Factual Research & Claim Verification
  reasoning_research:
    provider: openrouter
    model: deepseek/deepseek-r1
    temperature: 0.60
    max_tokens: 6000
    timeout: 180.0

  # R4.1: Narrative Scriptwriting & Creator DNA Emulation
  creative_script:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.75
    max_tokens: 3500

  # R4.1: Acoustic Voice QA & Timing Analysis
  acoustic_eval:
    provider: anthropic
    model: claude-3-5-haiku-20241022
    temperature: 0.15
    max_tokens: 1000

# Fallback provider chain for all auxiliary requests
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-3-5-haiku
  - provider: deepseek
    model: deepseek-chat
```

---

### 3.3 Domain Code Request Pattern via `ModelRuntime` & `CapabilityBridge`

To ensure zero tight coupling, H9 domain modules request role execution through optional dependency injection of `HermesCapabilityBridge` or `ModelRuntime`:

```python
# Pattern Example: src/editorial/angle_generator.py with ModelRuntime integration
class AngleGenerator:
    def __init__(
        self,
        scorer: Optional[EditorialScorer] = None,
        bridge: Optional[HermesCapabilityBridge] = None,
    ):
        self.scorer = scorer or EditorialScorer()
        self.bridge = bridge

    def generate_candidates(
        self,
        dossier: ResearchDossier,
        brief: Optional[ContentBrief] = None,
        creator: Optional[CreatorProfile] = None,
        offline: bool = False,
    ) -> List[EditorialAngle]:
        # 1. If bridge is available and not offline, request model completion via FAST_EDITORIAL
        if self.bridge and not offline:
            try:
                system_instruction = (
                    "You are the Harness 9 Editorial Engine. Generate 5 orthogonal candidate angles "
                    "across archetypes: contrarian, deep_dive, data_led, human_narrative, future_impact."
                )
                prompt = f"Topic: {dossier.topic}\nHeadline: {dossier.headline}\nClaims: {dossier.claims}"
                
                # Structured schema invocation
                resp = self.bridge.invoke_capability(
                    role=CapabilityRole.FAST_EDITORIAL,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    schema=CandidateAnglesResponseSchema,
                    temperature=0.35,
                )
                if resp.parsed and resp.parsed.angles:
                    return resp.parsed.angles
            except Exception as exc:
                logger.warning(f"Fast editorial model invocation failed, falling back to heuristics: {exc}")

        # 2. Deterministic heuristic fallback (preserves offline reproducibility and test speed)
        return self._generate_candidates_heuristic(dossier, brief, creator)
```

---

### 3.4 Runtime Execution Call Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 H9 Domain Module (e.g. AngleGenerator / ScriptGenerator)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ calls bridge.invoke_capability(role, prompt, schema)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               src/h9_runtime/bridge.py (HermesCapabilityBridge)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ delegates to self._models.invoke_capability(...)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              src/h9_runtime/models.py (DefaultModelRuntime)                 │
│  • Reads role configuration (fallback to DEFAULT_ROLE_CONFIGS)              │
│  • Calculates token estimate & checks session budget limit                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ calls agent.auxiliary_client.call_llm(...)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              agent/auxiliary_client.py (_call_llm_impl)                     │
│  • Resolves config: auxiliary.<role> in ~/.hermes/config.yaml               │
│  • Acquires concurrency semaphore for task                                  │
│  • Dispatches via cached provider client (chat_completions / anthropic)      │
│  • On HTTP 429/402: rotates credential pool or tries fallback_providers     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ returns response (content + usage)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              DefaultModelRuntime: records usage in BudgetStatus,            │
│              validates against Pydantic schema, returns ModelResponse       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Caveats

1. **Network Independence for Unit Tests**:
   - Hermes CI tests must run without requiring live network calls or active API keys.
   - `DefaultModelRuntime` must retain its offline/mock generation mode when no credentials exist or when running in offline unit tests (`offline=True`), while seamlessly delegating to `auxiliary_client.call_llm` when configured.
2. **Audio Generation vs LLM Inference**:
   - `OpenAIAudioProvider` in `src/scriptwriting/voice_director.py` calls the OpenAI Audio speech API (`/v1/audio/speech`). This is an audio TTS endpoint, not an LLM chat completion endpoint.
   - While text generation routes through `ModelRuntime`, audio providers should resolve credentials safely via `agent.secret_scope.get_secret("OPENAI_API_KEY")` rather than raw `os.getenv`, and fall back cleanly to procedural Harmonic audio in offline modes.
3. **Pydantic Schema Serialization**:
   - `ModelRuntime` accepts generic Pydantic models (`Type[T]`). When invoking structured responses through OpenAI-compatible or Anthropic providers, tools/structured outputs format or JSON schema extraction must handle both Pydantic v1 (`__fields__`) and v2 (`model_fields`).

---

## 5. Conclusion

1. **Provider System Alignment**: Hermes possesses a mature declarative provider profile registry (`providers/base.py`, 39 bundled plugins in `plugins/model-providers/`) and an auxiliary client router (`agent/auxiliary_client.py:call_llm`) with automatic fallback chains, credit exhaustion recovery, and per-task config overrides (`auxiliary.<task>`).
2. **H9 Clean Separation**: H9 domain code in `src/` currently uses deterministic heuristics and templates, with no hardcoded LLM SDK instantiations. Only `voice_director.py` had an un-gated HTTP endpoint call for TTS audio.
3. **Runtime Bridge Ready**: `src/h9_runtime/models.py` and `src/h9_runtime/bridge.py` already establish the `ModelRuntime` protocol and `CapabilityRole` enum.
4. **Actionable Implementation Path**: Milestone 4 can directly bridge `DefaultModelRuntime.invoke_capability()` to `agent.auxiliary_client.call_llm(task=role.value, ...)`, allowing all 4 logical roles (`fast_editorial`, `reasoning_research`, `creative_script`, `acoustic_eval`) to be configured in `config.yaml` with automatic provider fallback, prompt caching protection, and spend accounting.

---

## 6. Verification Method

### 6.1 Inspecting Interface & Configuration Points
1. Inspect `src/h9_runtime/models.py` lines 60–85 to verify `DEFAULT_ROLE_CONFIGS` definitions for all 4 capability roles.
2. Inspect `agent/auxiliary_client.py` lines 8311–8360 to verify `_resolve_task_provider_model` handles task-based configuration resolution.
3. Inspect `hermes_cli/fallback_config.py` lines 80–102 to verify fallback chain merging.

### 6.2 Test Execution Commands
Run the unit test suite verifying protocol conformance and role budgeting:
```bash
uv run pytest tests/test_h9_runtime.py -v -k "test_07_model_runtime_roles_and_budgeting"
uv run pytest tests/test_h9_content_tools.py -v
```
*(Verified passing in environment: `tests/test_h9_runtime.py` test_07 passed 100%)*

### 6.3 Invalidation Conditions
- Any change that registers new core tools in `_HERMES_CORE_TOOLS` (violates Rung 3).
- Any change that mutates conversation history or system prompts mid-session (violates sacred prompt caching).
- Direct instantiation of `openai.OpenAI()` or `anthropic.Anthropic()` inside `src/editorial/`, `src/research/`, or `src/scriptwriting/` (violates decoupled runtime boundary).
