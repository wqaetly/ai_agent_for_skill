import { HumanInterrupt } from "@langchain/langgraph/prebuilt";

export function isAgentInboxInterruptSchema(
  value: unknown,
): value is HumanInterrupt | HumanInterrupt[] {
  const valueAsObject = Array.isArray(value) ? value[0] : value;
  if (!valueAsObject || typeof valueAsObject !== "object") {
    return false;
  }

  const interrupt = valueAsObject as Record<string, unknown>;
  if (!interrupt.value || typeof interrupt.value !== "object") {
    return false;
  }

  const hitlValue = interrupt.value as Record<string, unknown>;
  const { action_requests: actionRequests, review_configs: reviewConfigs } =
    hitlValue;

  if (!Array.isArray(actionRequests) || actionRequests.length === 0) {
    return false;
  }
  if (!Array.isArray(reviewConfigs) || reviewConfigs.length === 0) {
    return false;
  }

  const hasValidActionRequests = actionRequests.every((request) => {
    return (
      request &&
      typeof request === "object" &&
      "name" in request &&
      typeof request.name === "string" &&
      "args" in request &&
      request.args !== null &&
      typeof request.args === "object"
    );
  });

  const hasValidConfigs = reviewConfigs.every((config) => {
    return (
      config &&
      typeof config === "object" &&
      "action_name" in config &&
      typeof config.action_name === "string" &&
      "allowed_decisions" in config &&
      Array.isArray(config.allowed_decisions)
    );
  });

  return hasValidActionRequests && hasValidConfigs;
}
