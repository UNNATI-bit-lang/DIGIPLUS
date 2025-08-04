import networkx as nx
import random

class NetworkSimulator:
    def _init_(self):
        self.G = nx.Graph()
        self.create_topology()
        self.traffic_rates = {
            '08:00': {'A': 50, 'B': 30, 'C': 40, 'D': 20, 'E': 60},
            '08:15': {'A': 55, 'B': 35, 'C': 45, 'D': 25, 'E': 65},
            '08:30': {'A': 60, 'B': 40, 'C': 50, 'D': 30, 'E': 70},
            '08:45': {'A': 55, 'B': 35, 'C': 45, 'D': 25, 'E': 65}
        }
        self.time_keys = list(self.traffic_rates.keys())
        self.time_index = 0
        self.packet_queues = {node: [] for node in self.G.nodes}
        self.link_loads = {edge: 0 for edge in self.G.edges}

    def create_topology(self):
        self.G.add_nodes_from(['A', 'B', 'C', 'D', 'E'])
        self.G.add_edge('A', 'B', capacity=100)
        self.G.add_edge('A', 'C', capacity=80)
        self.G.add_edge('B', 'D', capacity=70)
        self.G.add_edge('C', 'D', capacity=90)
        self.G.add_edge('C', 'E', capacity=100)
        self.G.add_edge('D', 'E', capacity=60)

    def step(self):
        time_slot = self.time_keys[self.time_index]
        rates = self.traffic_rates[time_slot]
        self.link_loads = {edge: 0 for edge in self.G.edges}

        # generate packets at each node
        for node, rate in rates.items():
            for _ in range(rate):
                dest = random.choice([n for n in self.G.nodes if n != node])
                path = nx.shortest_path(self.G, source=node, target=dest)
                self.transmit(path)

        self.time_index = (self.time_index + 1) % len(self.time_keys)
        return time_slot

    def transmit(self, path):
        for i in range(len(path) - 1):
            edge = tuple(sorted((path[i], path[i+1])))
            cap = self.G.edges[edge]['capacity']
            if self.link_loads[edge] < cap:
                self.link_loads[edge] += 1
            else:
                # queue at node
                self.packet_queues[path[i]].append(path)
                break

    def get_graph(self):
        return self.G

    def get_link_loads(self):
        return self.link_loads

    def get_queues(self):
        return {k: len(v) for k, v in self.packet_queues.items()}

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from simulation import NetworkSimulator

st.set_page_config(layout='wide')
sim = st.session_state.get('sim', None)

if not sim:
    sim = NetworkSimulator()
    st.session_state.sim = sim

st.title("📡 Network Traffic Simulator - Python Version")

if st.button("▶ Run Next Time Slot"):
    current_time = sim.step()
    st.success(f"⏰ Simulated Time: {current_time}")

# --- Visualization ---
G = sim.get_graph()
link_loads = sim.get_link_loads()
queues = sim.get_queues()
pos = nx.spring_layout(G, seed=42)

# Create graph with Plotly
edge_x = []
edge_y = []
colors = []
for (u, v) in G.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    load = link_loads[(u, v)] if (u, v) in link_loads else link_loads[(v, u)]
    colors.append(min(255, load))

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=2, color='gray'),
    hoverinfo='none',
    mode='lines'
)

node_x = []
node_y = []
labels = []
for node in G.nodes():
x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    labels.append(f"{node}<br>Queue: {queues[node]}")

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=[f"{node}" for node in G.nodes()],
    textposition="bottom center",
    marker=dict(
        showscale=True,
        colorscale='Blues',
        size=30,
        color=[queues[n] for n in G.nodes()],
        colorbar=dict(
            thickness=15,
            title='Packets in Queue',
            xanchor='left',
            titleside='right'
        )
    ),
    hoverinfo='text',
    hovertext=labels
)

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='Network Topology',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False))
               )

st.plotly_chart(fig, use_container_width=True)

# Show stats
st.subheader("📊 Node Queues")
st.table(queues)

st.subheader("🔗 Link Loads")
st.table(link_loads)