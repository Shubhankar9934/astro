# Class diagrams

Diagrams focus on types that span **decision**, **services**, and **storage**. Agent classes are numerous; see [Modules: agents](../modules/agents.md).

## Decision context and state

```mermaid
classDiagram
  class DecisionContext {
    +str symbol
    +str as_of
    +str market_summary
    +Optional~ModelPrediction~ model
    +dict extra
  }
  class ModelPrediction {
    +float p_up
    +float uncertainty
    +dict raw
  }
  class AstroState {
    +str company_of_interest
    +str trade_date
    +DecisionContext context
    +dict investment_debate_state
    +dict risk_debate_state
    +str final_trade_decision
  }
  DecisionContext *-- ModelPrediction : optional
  AstroState *-- DecisionContext
```

## Executor and configuration

```mermaid
classDiagram
  class AstroConfig {
    +dict system
    +dict agents
    +dict model
    +dict risk
    +dict ibkr
    +data_root_path(cwd) Path
  }
  class DecisionExecutor {
    +AstroConfig config
    +run(symbol, trade_date, context, mode) Tuple
    +from_config(config, log_dir) DecisionExecutor
    +run_analysts_only(...)
    +run_research_only(...)
    +run_risk_only(state_dict)
  }
  DecisionExecutor --> AstroConfig
```

## API dependencies (singletons)

```mermaid
classDiagram
  class get_config {
    <<function>>
    +returns AstroConfig
  }
  class get_executor {
    <<function>>
    +returns DecisionExecutor
  }
  class get_feature_service {
    <<function>>
    +returns FeatureService
  }
  get_config --> AstroConfig
  get_executor --> DecisionExecutor
```

## Storage

```mermaid
classDiagram
  class MetadataDB {
    +Path path
    +insert_decision(...)
    +get_decision(id)
    +log_experiment(...)
    +positions_max_updated_at()
    +close()
  }
```
