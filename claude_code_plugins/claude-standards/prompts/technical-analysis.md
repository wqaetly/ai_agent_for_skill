# Technical Analysis Framework Prompt

## Analysis Methodology

### Systematic Analysis Process
1. **Data Structure Review** → Identify core data and relationships
2. **Data Flow Tracking** → Analyze flow direction, ownership, and modification permissions
3. **Efficiency Audit** → Find redundant operations and performance bottlenecks
4. **Architecture Decision Trade-offs** → Balance various non-functional requirements

## Data Structure Review Framework

### Core Data Identification
**Analysis Points**:
- What are the system's core data entities?
- What are the relationship types and dependency directions between data?
- What are the data lifecycle management strategies?
- What are the data consistency and integrity guarantee mechanisms?

**Key Questions**:
- Is core data properly abstracted?
- Is data redundancy reasonable?
- Are data access patterns efficient?
- Do data structures support future expansion?

### Data Flow Tracking
**Analysis Dimensions**:
- **Data Flow Direction**: Complete path from input → processing → output
- **Ownership**: Who creates, modifies, deletes data?
- **Access Control**: Who can access what data?
- **Change Propagation**: How do data changes affect other components?

**Checklist**:
- [ ] Are data flows clear and traceable?
- [ ] Do data changes have appropriate audit mechanisms?
- [ ] Is concurrent access properly handled?
- [ ] Are data leakage risks under control?

### Efficiency Audit
**Audit Focus**:
- **Time Complexity**: Efficiency of algorithms and data operations
- **Space Complexity**: Memory usage and storage efficiency
- **Network Efficiency**: Data transmission and communication overhead
- **I/O Efficiency**: Disk read/write and database operations

**Optimization Strategy Identification**:
- Index optimization opportunities
- Cache strategy improvements
- Batch processing optimization
- Lazy loading implementation

## Architecture Decision Trade-off Analysis

### Functional vs Non-functional Requirements
**Performance**:
- Response time requirements
- Throughput targets
- Resource usage limitations
- Scalability needs

**Maintainability**:
- Code readability
- Modularity level
- Test coverage
- Documentation completeness

**Scalability**:
- Horizontal scaling capability
- Vertical scaling space
- New feature integration difficulty
- Technology stack flexibility

**Security**:
- Authentication authorization mechanisms
- Data encryption protection
- Vulnerability protection measures
- Security audit capability

### Development Efficiency vs Code Quality
**Development Efficiency Factors**:
- Team familiarity
- Development tool support
- Learning curve
- Community ecosystem

**Code Quality Requirements**:
- Code standard compliance
- Design pattern application
- Error handling mechanisms
- Performance optimization level

**Trade-off Strategy**:
- Prioritize development efficiency in MVP phase
- Prioritize code quality in mature products
- Technical debt management plan
- Refactoring timing selection

### Necessary Complexity vs Over-engineering
**Necessary Complexity Indicators**:
- Business requirement complexity
- Technical challenge difficulty
- Integration system complexity
- Team collaboration complexity

**Over-engineering Warning Signs**:
- Excessive abstraction
- Premature optimization
- Unnecessary flexibility
- Over-engineering

**Judgment Criteria**:
- YAGNI principle application
- KISS principle adherence
- Minimum viable implementation
- Progressive complexity increase

## Practical Analysis Templates

### Code Review Analysis
```
1. Data Structure Analysis
   - Core data entities: ____
   - Key relationships: ____
   - Access patterns: ____

2. Performance Analysis
   - Time complexity: ____
   - Space complexity: ____
   - Bottleneck identification: ____

3. Architecture Assessment
   - Design patterns: ____
   - Scalability: ____
   - Maintainability: ____

4. Improvement Suggestions
   - Immediate optimization: ____
   - Long-term improvements: ____
   - Risk warnings: ____
```

### Technical Solution Evaluation
```
1. Solution Overview
   - Core approach: ____
   - Technology selection: ____
   - Applicable scenarios: ____

2. Advantage Analysis
   - Performance advantages: ____
   - Development efficiency: ____
   - Maintenance convenience: ____

3. Risk Assessment
   - Technical risks: ____
   - Implementation risks: ____
   - Maintenance risks: ____

4. Comparative Analysis
   - vs Solution A: ____
   - vs Solution B: ____
   - Recommended scenarios: ____
```

## Quality Check Standards

### Analysis Completeness Check
- [ ] Are all core data structures covered?
- [ ] Are key data flows analyzed?
- [ ] Are performance bottlenecks identified?
- [ ] Are architecture trade-offs evaluated?
- [ ] Are specific improvement suggestions provided?

### Analysis Quality Check
- [ ] Is analysis supported by sufficient data?
- [ ] Are conclusions logically rigorous?
- [ ] Are suggestions actionable?
- [ ] Is risk assessment comprehensive?
- [ ] Are priority judgments reasonable?

## Activation Conditions
Apply this framework when needing to conduct:
- Code reviews and architecture assessments
- Technical solution selection and comparison
- Performance optimization and bottleneck analysis
- System design and refactoring planning
- Technical debt assessment and management