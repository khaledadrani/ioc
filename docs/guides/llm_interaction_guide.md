# LLM Interaction Guide

## Best Practices for Working with AI Assistants

### Session Preparation

#### Before Starting
1. **Review existing documentation** - Check analysis and guides for context
2. **Define clear objectives** - What specific outcome do you want?
3. **Gather relevant files** - Have code, tests, and docs ready to share
4. **Set scope boundaries** - What's in/out of scope for this session?

#### Context Sharing
- Share the most relevant existing documentation first
- Include current code state and test files
- Mention any constraints or requirements
- Reference previous work sessions if building on them

### During the Session

#### Effective Communication
- **Be specific** - "Add error handling" vs "Add ConventionInjectionError for missing providers"
- **Provide examples** - Show desired input/output or behavior
- **Ask for clarification** - If the approach seems unclear, ask for explanation
- **Iterate incrementally** - Build features step by step rather than all at once

#### Code Review Process
1. **Understand the approach** before implementation
2. **Review generated code** for correctness and style
3. **Test immediately** - Run tests after each significant change
4. **Provide feedback** - What works, what doesn't, what could be better

#### Decision Making
- **Document trade-offs** - Ask the LLM to explain pros/cons of different approaches
- **Consider alternatives** - "What other ways could we implement this?"
- **Think about future impact** - "How will this affect other parts of the system?"

### Common Patterns

#### Feature Implementation
1. **Analysis** - "Compare our current approach with [framework X]"
2. **Design** - "What's the best way to implement [feature Y]?"
3. **Implementation** - "Let's implement the design we discussed"
4. **Testing** - "Add comprehensive tests for the new feature"
5. **Documentation** - "Update the docs to reflect these changes"

#### Debugging Sessions
1. **Problem description** - Share error messages and context
2. **Root cause analysis** - "Why is this happening?"
3. **Solution exploration** - "What are our options to fix this?"
4. **Implementation** - Apply the chosen fix
5. **Verification** - Test that the fix works and doesn't break anything else

#### Architecture Reviews
1. **Current state analysis** - "How does our architecture compare to [standard]?"
2. **Gap identification** - "What are we missing?"
3. **Prioritization** - "What should we implement first?"
4. **Planning** - "How should we approach implementing [feature]?"

### Documentation During Sessions

#### Real-time Notes
- Keep track of key decisions and rationale
- Note any failed approaches and why they didn't work
- Document insights and "aha" moments
- Record any new understanding of the problem domain

#### Post-session Cleanup
- Create/update work session document using the template
- Update relevant analysis documents with new information
- Add or modify implementation guides based on what was learned
- Update the main README if the documentation structure changed

### Quality Assurance

#### Code Quality
- **Follow existing patterns** - Maintain consistency with current codebase
- **Add proper tests** - Don't just implement, verify it works
- **Update documentation** - Keep guides and examples current
- **Consider edge cases** - What could go wrong?

#### Documentation Quality
- **Be specific** - Avoid vague descriptions
- **Include examples** - Show, don't just tell
- **Link related content** - Connect to other relevant docs
- **Update status indicators** - Keep ✅❌⚠️ symbols current

### Common Pitfalls to Avoid

#### Over-engineering
- Don't implement more than needed for the current requirement
- Avoid premature optimization
- Keep solutions simple and focused

#### Under-documenting
- Don't skip documenting design decisions
- Always explain the "why" not just the "what"
- Include failed approaches and lessons learned

#### Inconsistent Style
- Follow existing code patterns and naming conventions
- Maintain consistent documentation formatting
- Use established error handling patterns

### Session Types

#### 🔨 Implementation Sessions
**Goal:** Build new features or fix bugs
**Focus:** Code quality, testing, documentation
**Output:** Working code + tests + updated docs

#### 📊 Analysis Sessions  
**Goal:** Understand problems or compare approaches
**Focus:** Research, comparison, decision making
**Output:** Analysis documents, recommendations

#### 🧠 Planning Sessions
**Goal:** Design architecture or plan implementation
**Focus:** Design decisions, trade-offs, roadmap
**Output:** Design documents, implementation plans

#### 🐛 Debugging Sessions
**Goal:** Fix issues or understand problems
**Focus:** Root cause analysis, solution verification
**Output:** Bug fixes, improved error handling

### Measuring Success

#### Immediate Success
- ✅ Objective achieved
- ✅ Code works and tests pass
- ✅ Documentation updated
- ✅ No regressions introduced

#### Long-term Success
- ✅ Solution is maintainable
- ✅ Approach is consistent with architecture
- ✅ Knowledge is captured for future reference
- ✅ Team can understand and extend the work