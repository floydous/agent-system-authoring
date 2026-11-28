# Primary Source Verification Log

**Audit Date**: 2026-11-22 (with 2026-11-23 JSON Schema validation-keyword addenda, 2026-11-26 Gemini `parametersJsonSchema` addendum, and 2026-11-27 gateway model-slug provenance record)  
**Purpose**: Records primary-source verification for every specification, vendor document, and peer-reviewed paper cited in `agent-system-authoring`. Under the repository evidence policy, quantitative metrics may appear in the skill only if recomputed from `evidence/raw/` traces (`phase_a/`, `phase_b/`, `phase_c/`, `phase_d/`, `phase_e/`, `h08_particle1/`, `phase_f_nemo/`, `phase_f_ling/`, `phase_g_luna/`, `evals_v4/`, `pi_agent_eval/`) or present in retrieved source text below.

---

## 1. Open Specifications & Standards (Tier 1)

### 1.1 Agent Skills Specification (`R-SKILL-01`, `R-SKILL-02`, `R-SKILL-03`, `R-SKILL-04`)
- **URL**: `https://agentskills.io/specification` (`https://agentskills.io/specification.md`)
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Exact Facts & Quotes**:
  - Directory structure: `"A skill is a directory containing, at minimum, a SKILL.md file"`, with optional directories `scripts/`, `references/`, `assets/`. Note: `evals/` is NOT part of the open specification (it is our project convention).
  - `name` field: Required; 1–64 characters; lowercase alphanumeric (`a-z`, `0-9`) and hyphens (`-`) only; must not start or end with `-`, no consecutive `--`; must match parent directory name.
  - `description` field: Required; max `1024` characters; non-empty; `"Describes what the skill does and when to use it."` Note: `"third person"` is NOT in `agentskills.io/specification.md` (see Anthropic Best Practices below).
  - `compatibility` field: Optional; max `500` characters.
  - Progressive disclosure: `"Instructions (< 5000 tokens recommended): The full SKILL.md body is loaded when the skill is activated"` and `"Keep your main SKILL.md under 500 lines. Move detailed reference material to separate files."`
  - File references: `"Keep file references one level deep from SKILL.md. Avoid deeply nested reference chains."`
- **Remediations Applied**: Dropped `"strictly disallow"` / `"guarantees deterministic"` (`R-SKILL-04`), dropped `"eliminates false-positive triggering"` (`R-SKILL-03`), dropped `"enterprise production readiness"` as a spec claim (`R-SKILL-01`).

### 1.2 Agent Skills Optimization Guide
- **URL**: `https://agentskills.io/skill-creation/optimizing-descriptions.md` and `https://agentskills.io/skill-creation/best-practices.md`
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Facts**: Reinforces keeping `SKILL.md` under `500` lines and `5,000` tokens, moving detailed reference material to separate files, and pairing positive triggers with near-miss negative test queries.

### 1.3 Anthropic Skill Authoring Best Practices (`R-SKILL-03` third-person note)
- **URL**: `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md`
- **Retrieved**: 2026-11-22 (web extraction)
- **Verified Quote**: `"Always write in third person. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems."` Also confirms max `64` chars for `name` and max `1,024` chars for `description`.

### 1.4 PEP 723 – Inline Script Metadata (`R-SKILL-06`)
- **URL**: `https://peps.python.org/pep-0723/` (superseded into live canonical spec `https://packaging.python.org/en/latest/specifications/inline-script-metadata/`)
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Quote**: Example metadata block uses `# /// script`, `# requires-python = ...`, `# dependencies = [...]`, `# ///`. Document defines top-level keys `dependencies`, `requires-python`, and optional `[tool]` table.

### 1.5 OpenAI Structured Outputs Guide (`R-TOOL-05`, `R-TOOL-06`, `R-TOOL-07`, `R-TOOL-10`)
- **URL**: `https://developers.openai.com/api/docs/guides/structured-outputs.md` (redirected from `https://platform.openai.com/docs/guides/structured-outputs`)
- **Retrieved**: 2026-11-22 & 2026-11-23 (HTTP 200 direct fetch)
- **Verified Quotes**:
  - `strict: true` constraints: `"additionalProperties: false must always be set in objects"` and `"All fields must be required"`, using nullable union types (`"anyOf"` or `["string", "null"]`) to emulate optional parameters.
  - Supported JSON Schema validation keywords (retrieved 2026-11-23):
    - `string`: `"pattern"` (regex) and `"format"` (`date-time`, `time`, `date`, `duration`, `email`, `hostname`, `ipv4`, `ipv6`, `uuid`). `minLength`/`maxLength` are not listed in supported string properties.
    - `number` / `integer`: `"multipleOf"`, `"maximum"`, `"exclusiveMaximum"`, `"minimum"`, `"exclusiveMinimum"`.
    - `array`: `"minItems"`, `"maxItems"`. *(Note: these type-specific constraints are marked not yet supported for fine-tuned models.)*
  - Enum support & documented numeric limits: `"A schema may have up to 1000 enum values across all enum properties. For a single enum property with string values, the total string length of all enum values cannot exceed 15,000 characters when there are more than 250 enum values."` Also: up to `5000` object properties total, up to `10` levels of nesting, max `120,000` total string chars across property/definition/enum/const names.
- **Remediations Applied**: Removed invented `≤ 20` enum threshold and fabricated `+15–25 pp` / `10%–25%` figures from `R-TOOL-06`; grounded large-enum guidance in OpenAI's documented `250`/`1000`/`15,000` bounds plus Google's state-machine rejection doc (`R-TOOL-07`); documented natively enforced OpenAI validation keywords (`pattern`, `format`, numeric bounds, array bounds).

### 1.6 Anthropic Structured Outputs & Strict Tool Use (`R-TOOL-05`, `R-TOOL-10`)
- **URL**: `https://platform.claude.com/docs/en/build-with-claude/structured-outputs` (referencing `https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use`)
- **Retrieved**: 2026-11-22 & 2026-11-23 (web extraction)
- **Verified Quotes & Constraints**:
  - `strict: true` constraints: `required` and `"additionalProperties"` (`"must be set to false for objects"`) are supported, while optional parameters omitted from `required` are allowed (unlike OpenAI, where every property must be in `required`). Top-level `"strict": true` sits on the tool object alongside `input_schema`.
  - JSON Schema validation keyword limitations (retrieved 2026-11-23):
    - Supported: string `format` (`date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`), array `minItems` (`0` and `1` only), and simple regex `pattern` (`*`, `+`, `?`, simple `{n,m}`, character classes, groups — no backreferences `\1`/`\2`, lookahead/lookbehind `(?=...)`/`(?!...)`, word boundaries `\b`/`\B`, or complex `{n,m}` large ranges).
    - **Not supported** (triggers HTTP `400`): `"Numerical constraints (such as minimum, maximum, multipleOf)"`, `"String constraints (minLength, maxLength)"`, `"Array constraints beyond minItems of 0 or 1"`. Official SDK helpers transform unsupported constraints by removing them from the wire schema, appending them to field `description`s (e.g., `{minimum: 100}`), and validating responses client-side.
  - Documented compiled-grammar request limits across `output_config.format` and `strict: true` tools: `20` max strict tools per request; `24` max optional parameters (not listed in `required`) across all strict tool and JSON output schemas; `16` max parameters using union types (`anyOf` or `"type": ["string", "null"]`) across all strict schemas (`"These are especially expensive because they create exponential compilation cost"`). Guidance adds: `"Reduce optional parameters. Make parameters required where possible. Each optional parameter roughly doubles a portion of the grammar's state space."`
  - Property ordering caveat: `"When using structured outputs, properties in objects maintain their defined ordering from your schema, with one important caveat: required properties appear first, followed by optional properties."` (`"If property order in the output is important to your application, mark all properties as required, or account for this reordering in your parsing logic."`)
  - Enum capitalization caveat: Anthropic docs note case-insensitive enum matching may emit mismatched capitalization (e.g., `"Conversation Topic 3"`) without error, advising callers to compare case-insensitively and avoid enum values differing only by capitalization.

---

## 2. Vendor Engineering Documentation (Tier 3)

### 2.1 Anthropic Tool Use Best Practices (`R-TOOL-02`, `R-TOOL-03` incl. merged `R-TOOL-09`, `R-TOOL-08`, `R-TOOL-11`)
- **URL**: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools` (redirected from `https://docs.anthropic.com/en/docs/build-with-claude/tool-use/implement-tool-use`)
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Quotes**:
  - Descriptions (`R-TOOL-03`): `"Provide extremely detailed descriptions. This is by far the most important factor in tool performance. Your descriptions should explain every detail about the tool, including: What the tool does; When it should be used (and when it shouldn't); What each parameter means and how it affects the tool's behavior; Any important caveats or limitations... Aim for at least 3–4 sentences for each tool description, more if the tool is complex."`
  - Names (`R-TOOL-02`): `"Use meaningful namespacing in tool names. When your tools span multiple services or resources, prefix names with the service... This makes tool selection unambiguous"`
  - Consolidation (`R-TOOL-08`): `"Consolidate related operations into fewer tools... Fewer, more capable tools reduce selection ambiguity"`
  - Explanation vs reasoning parameters (`R-TOOL-11` nuance): `"If a parameter asks Claude why it is making the call, ask for a short explanation or the supporting evidence. A parameter that asks for the model's thinking or step-by-step reasoning might lead to a reasoning_extraction refusal."`
- **Remediations Applied**: Corrected `"2–4 concise sentences"` to Anthropic's actual `"at least 3–4 sentences"` (more if complex). Merged `R-TOOL-09` into `R-TOOL-03`.

### 2.2 Anthropic Prompting Best Practices — XML Tags (`R-SYS-08` T3 note)
- **URL**: `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices`
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Quote**: `"Structure prompts with XML tags — XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs. Wrapping each type of content in its own tag (for example, <instructions>, <context>, <input>) reduces misinterpretation."` Notes models including `Claude Fable 5.2` and `Claude Opus 5.5`. Advises nesting only when content has a natural hierarchy (`<documents><document index="n">`).

### 2.3 OpenAI Model Spec (`R-SYS-03`)
- **URL**: `https://model-spec.openai.com/` (`https://model-spec.openai.com/2025-02-12.html`)
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Quotes**:
  - `"The chain of command, roles determine the authority of instructions in the case of conflicts: system ... developer ... user ... assistant ... tool"`
  - `"Ignore untrusted data by default, all other content (e.g., untrusted_text, quoted text, images, or tool outputs) should be ignored unless an applicable higher-level instruction explicitly delegates authority to it."`

### 2.4 OpenAI Reasoning Best Practices (`R-SYS-07`, `R-SYS-09`)
- **URL**: `https://developers.openai.com/api/docs/guides/reasoning-best-practices.md` & `https://developers.openai.com/api/docs/guides/reasoning.md`
- **Retrieved**: 2026-11-22 (HTTP 200 direct fetch)
- **Verified Quotes**:
  - `"Avoid chain-of-thought prompts: Since these models perform reasoning internally, prompting them to 'think step by step' or 'explain your reasoning' is unnecessary."` And: `"instructing the model to 'think step by step,' may not enhance performance (and can sometimes hinder it)."`
  - Delimiters (`R-SYS-08`): `"Use delimiters like markdown, XML tags, and section titles to clearly indicate distinct parts of the input"`
  - Few-shot (`R-SYS-09`): `"Try zero shot first, then few shot if needed... ensure that the examples align very closely with your prompt instructions, as discrepancies between the two may produce poor results."`
  - Also references `gpt-6-luna` and `gpt-6.2-astra` in `reasoning.md`.
- **Remediations Applied**: Removed `"officially deprecates"`.

### 2.5 Google Gemini / Vertex AI Structured Outputs & Function Calling (`R-TOOL-05`, `R-TOOL-06`, `R-TOOL-07`, `R-TOOL-10`)
- **URL**: `https://aistudio.google.com/docs/structured-output`, `https://ai.google.dev/gemini-api/docs/structured-output`, & `https://ai.google.dev/gemini-api/docs/function-calling`
- **Retrieved**: 2026-11-22, 2026-11-23 & 2026-11-26 (HTTP 200 direct fetch + web extraction)
- **Verified Quotes**:
  - Function declarations: passed with `name`, `description`, and either **`parametersJsonSchema`** (SDK: `parameters_json_schema`, standard JSON Schema object) or legacy **`parameters`** (`type`, `properties`, `required` array of mandatory parameter names — OpenAPI 3.0 subset). There is no OpenAI/Anthropic `"strict": true` toggle, and optional parameters are normally omitted from `required`.
  - **`parametersJsonSchema` addendum (verified 2026-11-26)**: Standard JSON Schema support in `FunctionDeclaration.parametersJsonSchema` natively supports `pattern` (simple regexes), `minimum`, `maximum`, `anyOf`, `$ref`, `type: "null"`, and `additionalProperties: false`. Complex regexes or deeply nested state machines can still trigger `400 INVALID_ARGUMENT`.
  - Legacy `parameters` (OpenAPI 3.0 subset, retrieved 2026-11-23): enforces `minimum` and `maximum` (for `number`/`integer`), `format` (such as `date-time`, `date`, `time` for `string`), and `minItems`/`maxItems` (for `array`); silently strips and ignores `minLength`, `maxLength`, `minProperties`, `maxProperties`, `uniqueItems`, `contains`, `minContains`, and `maxContains` during request normalization, and does not list `pattern` in the legacy OpenAPI subset.
  - Complex schema / `any`-mode limits: `"When you use any mode or define complex parameter schemas, the API compiles your function declarations into a state machine that constrains token generation. This state machine enforces limits on total states, branching paths, and nesting depth. If the combined complexity of your tools exceeds these limits, the API rejects the request with a 400 INVALID_ARGUMENT error."`
  - Schema simplification guidance: `"Move non-structural rules to descriptions: Field description properties and system instructions guide the model without adding states to the output grammar."` Further advises: `"Split large tool sets and move rules to descriptions"`, `"Flatten nested objects and bound recursion"`, `"Reduce branching from optional fields, enums, and anyOf: ... Mark properties as required where possible and allow null values when a field can be empty"`, and `"Shorten property names and drop array bounds"`.
  - Note: Google docs do NOT specify a `>20–50` enum cutoff or a `>30%` accuracy drop; both numbers were deleted.

---

## 3. Peer-Reviewed Literature & Preprints (Tier 4 & Tier 5)

Retrieved via live web extraction against `https://arxiv.org/abs/<id>` and web search on ACL Anthology / PMLR on 2026-11-22.

| Citation Key | Verified Title, Authors & Date | Verified Empirical Scope / Abstract Numbers | Discrepancies Corrected |
| :--- | :--- | :--- | :--- |
| `arXiv:2507.11538` | *How Many Instructions Can LLMs Follow at Once?* — Daniel Jaroslawicz, Brendan Whiting, Parth Shah, Karime Maamari (Submitted 15 Jul 2025) | **IFScale**: 500 keyword-inclusion instructions (scaling density); 20 models across 7 providers; best models achieve `68%` at 500 instructions; 3 decay patterns + primacy bias. | Removed unsupported `<= 10` rule cap and invented `15–20` threshold. |
| `arXiv:2509.21051` | *When Instructions Multiply* — Keno Harada, Yudai Yamazaki, Masachika Taniguchi, Edison Marrese-Taylor, Takeshi Kojima, Yusuke Iwasawa, Yutaka Matsuo (Submitted 25 Sep 2025, EMNLP Findings) | **ManyIFEval** (up to 10 instructions) & **StyleMBPP** (up to 6 instructions) across 10 LLMs; compliance consistently degrades as instruction count increases. | Removed unverified `100% -> 21% (-79 pp)`, `39%`, `48%` claims not in abstract. |
| `arXiv:2307.03172` | *Lost in the Middle* — Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang (Submitted 6 Jul 2023, revised 20 Nov 2023; TACL 2024) | Multi-doc QA & key-value retrieval; highest at start/end, degrades in middle. | Removed unsupported `>20% to 40%` figure. |
| `arXiv:2508.07479` | *Positional Biases Shift as Inputs Approach Context Window Limits* — Blerta Veseli, Julian Chibane, Mariya Toneva, Alexander Koller (Submitted 10 Aug 2025; COLM 2025) | LiM strongest up to `50%` of context window; beyond `50%`, primacy weakens and recency distance-based bias dominates. | Retained `50%` threshold; removed `>20% degradation avoided`. |
| `arXiv:2404.13208` | *The Instruction Hierarchy* — Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, Alex Beutel (Submitted 19 Apr 2024) | Tested on `GPT-3.5`; increases robustness against unseen attacks with minimal standard capability degradation. | Removed `up to 63% attack reduction` (not in abstract) and corrected models tested (`GPT-3.5`, not GPT-4/4o). |
| `arXiv:2603.23530` | *Did You Forget What I Asked? Prospective Memory Failures in Large Language Models* — Avni Mittal (Submitted 7 Mar 2026, revised 11 Jun 2026; ACL Anthology) | 3 model families, >`8,000` prompts; drops `2–21%` under concurrent load, terminal constraints drop up to `50%`, trailing reminder restores `90–100%`; GSM8K dropped `93%` to `27%`. | Removed fabricated `>10 turns` threshold from rule statement. |
| `arXiv:2209.12711` | *Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts* — Joel Jang, Seonghyeon Ye, Minjoon Seo (Submitted 26 Sep 2022) | 9 tasks; inverse scaling on OPT (`125M–175B`), GPT-3, InstructGPT. | Removed `~50%` flatline claim (not in abstract); corrected OPT upper size (`175B`, not `66B`). Promoted `R-SYS-05` to **T2** on `GPT 6 Luna` via `PB-4` and `PC-2` (refuting pre-2023 inverse scaling on explicit prohibitions). |
| `arXiv:2512.05858` | *Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy* — Savir Basil, Ina Shapiro, Dan Shapiro, Ethan Mollick, Lilach Mollick, Lennart Meincke (Submitted 5 Dec 2025) | 6 models evaluated on GPQA Diamond and MMLU-Pro; expert & low-knowledge personas tested. | Removed false attribution of exact `0.0%` / `+19.4%` bloat; aligned with title + abstract. |
| `arXiv:2311.10054` | *When "A Helpful Assistant" Is Not Really Helpful* — Mingqian Zheng, Jiaxin Pei, Lajanugen Logeswaran, Moontae Lee, David Jurgens (Submitted 16 Nov 2023, revised 9 Oct 2024) | `162` roles across `6` relationship types and `8` domains; `4` LLM families; `2,410` factual questions; personas do not improve overall performance over no-persona control. | Exact match verified. |
| `arXiv:2505.11423` | *When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following in LLMs* — Xiaomin Li, Zhou Yu, Zhiwei Zhang, Xupeng Chen, Ziji Zhang, Yingying Zhuang, Narayanan Sadagopan, Anurag Beniwal (Submitted 16 May 2025, revised 2 Sep 2025) | `15` models across `IFEval` and `ComplexBench`; consistent drops with CoT prompting. | Removed unverified `13 of 14 models` and `-16.2 pp on Llama-3-8B`. |
| `arXiv:2411.10541` | *Does Prompt Formatting Have Any Impact on LLM Performance?* — **Jia He**, Mukund Rungta, David Koleczek, Arshdeep Sekhon, Franklin X Wang, Sadid Hasan (Submitted 15 Nov 2024) | Tested Plain Text, Markdown, JSON, YAML (NOT XML) on GPT-3.5-turbo (up to `40%` variation on code translation) and GPT-4 (more robust). | Fixed first author citation to **He et al.** everywhere; removed `42%`. |
| `arXiv:2604.18389` | *Understanding the Prompt Sensitivity* — Yang Liu, Chenhui Chu (Submitted 20 Apr 2026) | Taylor expansion / logit variance analysis: prompt templates exert greater influence on logits than questions themselves. | Exact match verified. |
| `arXiv:2509.13196` | *The Few-shot Dilemma: Over-prompting Large Language Models* — Yongjian Tang, Doruk Tuncel, Christian Koerner, Thomas Runkler (Submitted 16 Sep 2025, revised 26 Jul 2026) | GPT-4o, GPT-3.5-turbo, DeepSeek-V3, Gemma-3, LLaMA-3.1, LLaMA-3.2, Mistral; excessive examples can degrade performance. | Removed fabricated `k ∈ [2, 4]` and `>85%` claims. |
| `arXiv:2602.04297` | *Revisiting Prompt Sensitivity in LLMs for Text Classification* — Branislav Pecher, Michal Spiegel, Robert Belanec, Jan Cegin (Submitted 4 Feb 2026) | Studies prompt underspecification variance in text classification (not few-shot rule overriding). | Removed from `R-SYS-09` conflicting-example justification; replaced with Camassa & Shiller (`2605.20382`, May 2026) & OpenAI guide. |
| `arXiv:2605.20382` | *Do as I Say, Not as I Do: Instruction-Induction Conflict in LLMs* — Carolina Camassa, Derek Shiller (Submitted 19 May 2026, via web search) | `13` models, `16` instructions; hardcoded conflicting assistant examples drop grand-mean IF rate to `27%` (fixed-output) / `43%` (task-based). | Added as verified support for keeping few-shot examples aligned with written constraints. |
| `arXiv:2506.09501` | *Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference* — Jiayi Yuan, Hao Li, Xinheng Ding, Wenya Xie, Yu-Jhe Li, Wentian Zhao, Kun Wan, Jing Shi, Xia Hu, Zirui Liu (Submitted 11 Jun 2025, revised 24 Oct 2025) | Floating-point non-associativity under BF16 greedy decoding; `DeepSeek-R1-Distill-Qwen-7B` showed up to `9%` accuracy variation and `9,000` token length difference across GPU/batch configs. | Verified `9%` and `9,000` token numbers directly in abstract. |
| `arXiv:2408.04667` | *Non-Determinism of "Deterministic" LLM Settings* — Berk Atil, Sarp Aykent, Alexa Chittams et al. (Submitted 6 Aug 2024, revised 2 Apr 2025; Eval4NLP) | `5` LLMs, `8` tasks, `10` runs; up to `15%` accuracy variation and up to `70%` best-worst gap; defines `TARr@N` and `TARa@N`. | Exact match verified. |
| `arXiv:2510.14972` | *TokDrift: When LLM Speaks in Subwords but Code Speaks in Grammar* — Yinxi Li, Yuntian Deng, Pengyu Nie (Submitted 16 Oct 2025) | `9` code LLMs (`>30B` params included); superficial formatting / identifier naming shifts BPE segmentation and model behavior. | Removed unverified `15%–40% fertility` and noted tool-call accuracy impact was not directly measured (`snake_case` is a convention on top of this T4 mechanism). |
| ACL `2026.acl-long.915` | *SubTokenTest: A Practical Benchmark for Real-World Sub-token Understanding* — Shuyang Hou, Yi Hu, Muhan Zhang (ACL 2026 Main, via web search) | `9` LLMs across `10` tasks / `4` domains; isolates subword tokenization failures. | Removed wrong venue/model attribution. |
| ACL `2025.ijcnlp-short.31` | *Broken Words, Broken Performance* — Sachin Pawar, Manoj Apte, Kshitij Jadhav, Girish Keshav Palshikar, Nitin Ramrakhiyani (IJCNLP-AACL 2025, via web search) | `4` open-source LLMs, `7` tasks; higher Contextual Penalty correlates with incorrect outputs (`17/28` dataset-LLM pairs at p<0.05). | Fixed exact venue to IJCNLP-AACL 2025 and cited retrieved metrics. |
| `arXiv:2408.04682` | *ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use Capabilities* — **Jiarui Lu**, Thomas Holleis, Yizhe Zhang et al. (Submitted 8 Aug 2024, revised 16 Apr 2025; NAACL 2025 Findings) | Includes "Tool name scrambling" (`send_message` -> `messages_0`) & removing argument descriptions; tested GPT-4, GPT-4o, Claude-3-Sonnet, Gemini-1.5. | Fixed wrong first author (`"Sun et al."` -> **`Lu et al.`**); removed unverified `>30%` delta. |
| BFCL / ICML 2025 | *The Berkeley Function Calling Leaderboard (BFCL)* — Shishir G. Patil, Huanzhi Mao, Fanjia Yan, Charlie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, Joseph E. Gonzalez (ICML 2025, PMLR v267; `https://gorilla.cs.berkeley.edu/leaderboard.html`) | Evaluates AST tool execution, multi-turn, and abstention (irrelevance). | Removed unverified `40% false-positive invocations`; merged `R-TOOL-09` into `R-TOOL-03`. |
| `arXiv:2602.20426` | *Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use* — Ruocheng Guo, Kaiwen Dong, Xiang Gao, Kamalika Das (Submitted 23 Feb 2026, revised 29 Apr 2026) | `150+` candidate tools; reduces scaling degradation by `29.23%` and improves average query-level success by `60.89%` on StableToolBench. | Exact match verified. |
| `arXiv:2505.18135` | *Tool Preferences in Agentic LLMs are Unreliable* — Kazem Faghih, Wenxiao Wang, Yize Cheng, Siddhant Bharti, Gaurang Sriramanan, Sriram Balasubramanian, Parsa Hosseini, Soheil Feizi (Submitted 23 May 2025, revised 21 Sep 2025; EMNLP 2025) | `17` models including `GPT-4.1` and `Qwen2.5-7B`; edited tool descriptions receive `>10x` more usage than original descriptions. | Exact match verified; bounded against `TS-1` confounds. |
| `arXiv:2505.10570` | *LongFuncEval* — Kiran Kate, Tejaswini Pedapati, Kinjal Basu, Yara Rizk, Vijil Chenthamarakshan, Subhajit Chaudhury, Mayank Agarwal, Ibrahim Abdelaziz (Submitted 30 Apr 2025) | Performance drops `7%` to `85%` as tool count increases, `7%` to `91%` as response length increases, and `13%` and `40%` on longer multi-turn conversations. | Fixed `85.5%` -> **`85%`**; removed invented `8K–120K`, `<= 10–20` cap, and `Top-3–Top-5`. |
| `arXiv:2307.16789` | *ToolLLM* — Yujia Qin, Shihao Liang, Yining Ye et al. (Submitted 31 Jul 2023, revised 3 Oct 2023; ICLR 2024) | ToolBench (`16,464` RESTful APIs across `49` categories) with a neural API retriever for large toolsets. | Exact match verified. |
| `arXiv:2601.07525` | *Thinking Before Constraining: A Unified Decoding Framework for Large Language Models* — Ngoc Trinh Hung Nguyen, Alonso Silva, Laith Zumot, Liubov Tupikina, Armen Aghasaryan, Mehwish Alam (Submitted **12 Jan 2026**, revised 28 May 2026) | Unconstrained reasoning before constrained structured decoding via trigger token; up to `27%` accuracy gain over natural generation. | Fixed citation date `"May 2026"` -> **`Jan 2026`**. |
| `arXiv:2408.02442` | *Let Me Speak Freely?* — Zhi Rui Tam, Cheng-Kuang Wu, Yi-Lin Tsai, Chieh-Yen Lin, Hung-yi Lee, Yun-Nung Chen (Submitted 5 Aug 2024, revised 14 Oct 2024; EMNLP 2024) | Significant decline in reasoning abilities under stricter format constraints vs free-form generation. | Removed unverified `11 open models` unless noted qualitatively. |

---

## 4. Empirical Benchmark Gateway Slugs & Model-Card Provenance (2026-11-27)

Every live JSONL record in `evidence/raw/` (except legacy Phase C v1.1.0 records noted in `evidence/README.md`) records the exact gateway/router model slug used during execution. Architecture, lineage, and parameter-count descriptions cited in router catalogs are **gateway metadata**, not primary-source model-card snapshots retrieved in Sections 1–3:

| Display Name Used in Reports | Exact Gateway / Router Slug in Traces | Trace Scope (`8,028` Benchmark + `490` Eval v4 + `85` Pi) | Provenance Note |
| :--- | :--- | :--- | :--- |
| `GPT 6 Luna` | `cx/gpt-6-luna` | Phases A–E (`3,098`) + Phase G (`1,280`) + Eval v4 (`490`) + Pi (`85` sessions) | Model name `gpt-6-luna` also appears in retrieved OpenAI `reasoning.md` (Section 2.4). |
| `Particle-1` | `openrouter/particle-ai/particle-1:free` | `H-08` replication (`950`) | Router slug verified directly in `raw/h08_particle1/results_H08-*.jsonl`; vendor/router lineage tag ("DeepSeek V4.1 Flash lineage") is unverified gateway metadata. |
| `Nemotron 3.5 Lightning` | `openrouter/nvidia/nemotron-3.5-lightning:free` | Phase F Nemotron (`1,190`) | Router slug verified directly in `raw/phase_f_nemo/results_NEMO-*.jsonl`; architecture/size tag (`30B-A3B` Mamba-2 SSM hybrid) is unverified gateway/catalog metadata. |
| `Ling 3.2 Flash` | `openrouter/inclusionai/ling-3.2-flash:free` | Phase F Ling (`1,510`) | Router slug verified directly in `raw/phase_f_ling/results_LING-*.jsonl`; architecture/size tag (`~560B-A25B` Hybrid-Linear KDA+MLA MoE) is unverified gateway/catalog metadata. |
