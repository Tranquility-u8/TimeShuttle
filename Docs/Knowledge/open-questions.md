# Open design and production questions

Agents must surface these when relevant rather than inventing answers.

- Which Drive document is the canonical living GDD? The current “Undingable - GameTitle GDD” appears largely template-based.
- What is the exact vertical-slice chapter/content boundary?
- Production Area Stop is still described as local in the older Drive snapshot, while the verified vertical slice is level-wide. What is the final spatial radius, and which actors beyond the player/current weapon are exempt?
- The vertical slice now uses uniform 10 points/second drain and recovery, no separate cooldown, toggle-to-cancel, a 70% FullStop threshold and auto-exit at zero. Are these production balance values, or prototype defaults to retune?
- What is the final weak-point state machine across normal, stopped, slowed, and resumed time?
- Should art receive a dedicated time-mode event/interface, or continue reading the ability component/HUD state? The first version intentionally has UI differentiation but no new VFX pass.
- Which additional interactables and physics classes require explicit FullStop exceptions beyond the verified weapon pickup and generic rigid body?
- Which features must be network-safe? Current materials suggest single-player, but this should be explicit.
- Which Unreal MCP implementation will the team standardize on, and which tools/actions are approved?
- Is Git LFS the final source-control path, or will the team move to Perforce as course material suggests?
- What is the canonical naming convention for new assets and Blueprint folders?
- What are the performance budgets and minimum target hardware for ray tracing/Lumen?
