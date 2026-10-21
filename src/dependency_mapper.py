import networkx as nx
import pandas as pd


class SubsystemDependencyMapper:

  def __init__(self):
    self.graph = nx.DiGraph()

  def build_correlation_graph(self, df, feature_cols, threshold=0.85):
    """Builds a directed dependency graph based on Pearson correlation

    among telemetry parameters across different subsystems during nominal flight.
    """
    # Compute correlation matrix
    corr_matrix = df[feature_cols].corr().abs()

    # Add nodes and edges where correlation exceeds the high threshold
    for i in range(len(corr_matrix.columns)):
      for j in range(i + 1, len(corr_matrix.columns)):
        col_i = corr_matrix.columns[i]
        col_j = corr_matrix.columns[j]
        weight = corr_matrix.iloc[i, j]

        if weight >= threshold:
          # Directed edge from source parameter to influenced parameter
          self.graph.add_edge(col_i, col_j, weight=round(float(weight), 2))

    print(
        f"Dependency Graph Built: {self.graph.number_of_nodes()} nodes, "
        f"{self.graph.number_of_edges()} dependency links established."
    )
    return self.graph

  def trace_cascading_impact(self, trigger_node, max_depth=2):
    """Traces downstream affected areas (subsystems/parameters) when a

    specific component, code change, or telecommand triggers an anomaly.
    """
    if trigger_node not in self.graph:
      return {
          "trigger": trigger_node,
          "immediately_affected": [],
          "downstream_affected": [],
      }

    # Find descendants within the specified propagation depth
    successors = nx.single_source_shortest_path_length(
        self.graph, trigger_node, cutoff=max_depth
    )

    impacted_nodes = list(successors.keys())
    # Separate immediate neighbors from deeper cascading impacts
    immediate = [
        node for node, depth in successors.items() if depth == 1
    ]
    downstream = [
        node for node, depth in successors.items() if depth > 1
    ]

    impact_report = {
        "trigger_source": trigger_node,
        "immediately_affected_areas": immediate,
        "temporal_downstream_areas": downstream,
        "total_affected_count": len(impacted_nodes) - 1,
    }

    return impact_report


# --- Example Integration ---
# mapper = SubsystemDependencyMapper()
# dependency_graph = mapper.build_correlation_graph(processed_df, feature_cols=['eps_voltage', 'adcs_gyro', 'tcs_temp'])
# report = mapper.trace_cascading_impact(trigger_node='eps_voltage')
# print(report)