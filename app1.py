
import pandas as pd
from sqlalchemy import create_engine, text
import os
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, dash_table, State, callback_context
# ----------------------
# 1. Data Handling 
# ----------------------
# Performing ETL
def load_and_clean_data(file_path):
    """Load and clean franchise data from Excel"""
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    
    # Rename columns to match expected format
    column_mapping = {
        'Group Name': 'FranchiseGroup',
        'Group Type': 'GroupType',  # New column
        'Country': 'Country',
        'Brand Name': 'Brand',
        'Brand Product Category': 'ProductType',
        'Brand country of Origin': 'BrandOrigin'  # New column
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Data validation
    df = df.drop_duplicates()
    df = df.dropna(subset=['Brand', 'FranchiseGroup', 'Country'])
    
    # Standardize categories
    if 'ProductType' in df.columns:
        df['ProductType'] = df['ProductType'].str.title()
    df['Country'] = df['Country'].str.upper()
    
    return df

# ----------------------
# 2. Database creation
# ----------------------
def setup_database(db_name='franchise.db'):
    """Set up SQLite database with proper schema"""
    engine = create_engine(f'sqlite:///{db_name}')
    
    # Create tables if not exists with modified schema to match the Excel file
    with engine.connect() as conn:
        # Use text() to make the SQL string executable
        sql = text("""
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT NOT NULL,
                franchise_group TEXT NOT NULL,
                country TEXT NOT NULL,
                product_type TEXT,
                group_type TEXT,
                brand_origin TEXT
            );
        """)
        conn.execute(sql)
        conn.commit()  # Commit the transaction
        
    return engine

def update_database(engine, df):
    """Update database with cleaned data"""
    # Map DataFrame columns to database columns
    column_mapping = {
        'Brand': 'brand_name',
        'FranchiseGroup': 'franchise_group',
        'Country': 'country',
        'ProductType': 'product_type',
        'GroupType': 'group_type',
        'BrandOrigin': 'brand_origin'
    }
    
    # Create a new DataFrame with only the columns we need
    df_db = pd.DataFrame()
    
    # Add each column we need, if it exists
    for src_col, db_col in column_mapping.items():
        if src_col in df.columns:
            df_db[db_col] = df[src_col]
        else:
            # If column doesn't exist, add empty column
            df_db[db_col] = None
    
    # Save to database
    df_db.to_sql('brands', engine, if_exists='replace', index=False)

# ----------------------
# 3. Dashboard Module
# ----------------------
def create_dashboard(engine):
    """Create interactive Dash dashboard"""
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    
    # Get initial data safely
    try:
        # Check which columns exist in the database
        db_columns = pd.read_sql("PRAGMA table_info(brands);", engine)['name'].tolist()
        
        # Check if columns exist for features
        has_country = 'country' in db_columns
        has_product_type = 'product_type' in db_columns
        has_brand_origin = 'brand_origin' in db_columns
        has_group_type = 'group_type' in db_columns
        
        # Get filtered dropdown options (no nulls)
        country_options = []
        if has_country:
            country_df = pd.read_sql("SELECT DISTINCT country FROM brands WHERE country IS NOT NULL", engine)
            country_options = [{'label': str(c), 'value': str(c)} for c in country_df['country'] if pd.notna(c)]
        
        product_options = []
        if has_product_type:
            product_df = pd.read_sql("SELECT DISTINCT product_type FROM brands WHERE product_type IS NOT NULL", engine)
            product_options = [{'label': str(p), 'value': str(p)} for p in product_df['product_type'] if pd.notna(p)]
        
        origin_options = []
        if has_brand_origin:
            origin_df = pd.read_sql("SELECT DISTINCT brand_origin FROM brands WHERE brand_origin IS NOT NULL", engine)
            origin_options = [{'label': str(o), 'value': str(o)} for o in origin_df['brand_origin'] if pd.notna(o)]
        
        group_options = []
        if has_group_type:
            group_df = pd.read_sql("SELECT DISTINCT group_type FROM brands WHERE group_type IS NOT NULL", engine)
            group_options = [{'label': str(g), 'value': str(g)} for g in group_df['group_type'] if pd.notna(g)]
    
    except Exception as e:
        print(f"Error loading initial data: {e}")
        has_country = has_product_type = has_brand_origin = has_group_type = False
        country_options = product_options = origin_options = group_options = []
    
    app.layout = html.Div([
        html.H1("Global Franchise Map Dashboard Demo", style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': '20px'}),
        
        html.Div([
            # Left panel - filters
            html.Div([
                html.H3("Search and Filters"),
                
                html.Label("Brand Search:"),
                dcc.Input(
                    id='search-input',
                    type='text',
                    placeholder='Search brands...',
                    style={'width': '100%', 'marginBottom': '15px'}
                ),
                
                html.Label("Country:") if has_country else html.Div(),
                dcc.Dropdown(
                    id='country-filter',
                    options=country_options,
                    multi=True,
                    placeholder='Filter by country',
                    style={'marginBottom': '15px'}
                ) if has_country else html.Div(),
                
                html.Label("Product Type:") if has_product_type else html.Div(),
                dcc.Dropdown(
                    id='product-filter',
                    options=product_options,
                    multi=True,
                    placeholder='Filter by product type',
                    style={'marginBottom': '15px'}
                ) if has_product_type else html.Div(),
                
                html.Label("Brand Origin:") if has_brand_origin and origin_options else html.Div(),
                dcc.Dropdown(
                    id='origin-filter',
                    options=origin_options,
                    multi=True,
                    placeholder='Filter by origin country',
                    style={'marginBottom': '15px'}
                ) if has_brand_origin and origin_options else html.Div(),
                
                html.Label("Group Type:") if has_group_type and group_options else html.Div(),
                dcc.Dropdown(
                    id='group-type-filter',
                    options=group_options,
                    multi=True,
                    placeholder='Filter by group type'
                ) if has_group_type and group_options else html.Div(),
                
            ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                      'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}),
            
            # Right panel - charts and table
            html.Div([
                html.Div([
                    html.Div(id='stats-cards', style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'})
                ]),
                
                html.Div([
                    dcc.Tabs([
                        # Table View Tab with Export Button
                        dcc.Tab(label='Table View', children=[
                            dash_table.DataTable(
                                id='brand-table',
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left', 'padding': '10px'},
                                style_header={'backgroundColor': '#007bff', 'color': 'white', 'fontWeight': 'bold'},
                                filter_action='native',
                                sort_action='native',
                                page_size=10
                            ),
                            # Export button - Enhancement 2
                            html.Div([
                                html.Button("Export Data to CSV", id="btn-export-csv", 
                                        style={'marginTop': '20px', 'backgroundColor': '#007bff', 'color': 'white', 
                                                'border': 'none', 'padding': '10px', 'borderRadius': '5px'}),
                                dcc.Download(id="download-dataframe-csv"),
                            ], style={'marginTop': '15px', 'textAlign': 'right'})
                        ]),
                        
                        # Global Map Tab - Enhancement 1
                        dcc.Tab(label='Global Map', children=[
                            html.Div([
                                html.H4("Global Brand Distribution", style={'textAlign': 'center'}),
                                dcc.Graph(id='world-map'),
                            ], style={'padding': '20px'})
                        ]),
                        
                        # Charts Tab
                        dcc.Tab(label='Charts', children=[
                            html.Div([
                                html.Div([
                                    html.H4("Brands by Country", style={'textAlign': 'center'}),
                                    dcc.Graph(id='country-chart')
                                ], style={'width': '50%'}),
                                
                                html.Div([
                                    html.H4("Brands by Product Type", style={'textAlign': 'center'}),
                                    dcc.Graph(id='product-chart')
                                ], style={'width': '50%'})
                            ], style={'display': 'flex', 'marginBottom': '20px'}),
                            
                            html.Div([
                                html.Div([
                                    html.H4("Brands by Origin", style={'textAlign': 'center'}),
                                    dcc.Graph(id='origin-chart')
                                ], style={'width': '100%'})
                            ]) if has_brand_origin and origin_options else html.Div()
                        ]),
                        
                        # Network View Tab - Enhancement 3
                        dcc.Tab(label='Network View', children=[
                            html.Div([
                                html.H4("Brand-Franchise Group Network", style={'textAlign': 'center'}),
                                dcc.Graph(id='network-graph', style={'height': '700px'}),
                            ], style={'padding': '20px'})
                        ]),
                        
                        # Analytics Tab - Enhancement 4
                        dcc.Tab(label='Analytics', children=[
                            html.Div([
                                html.H4("Brand Distribution Analytics", style={'textAlign': 'center'}),
                                
                                html.Div([
                                    # Product Category Distribution
                                    html.Div([
                                        html.H5("Product Category Distribution", style={'textAlign': 'center'}),
                                        dcc.Graph(id='product-treemap')
                                    ], style={'width': '50%'}),
                                    
                                    # Brand Concentration by Group
                                    html.Div([
                                        html.H5("Brand Concentration by Franchise Group", style={'textAlign': 'center'}),
                                        dcc.Graph(id='group-concentration')
                                    ], style={'width': '50%'})
                                ], style={'display': 'flex', 'marginBottom': '20px'}),
                                
                                html.Div([
                                    # Brand Origin vs Host Country Analysis
                                    html.Div([
                                        html.H5("Brand Origin vs Host Country Analysis", style={'textAlign': 'center'}),
                                        dcc.Graph(id='origin-host-analysis')
                                    ], style={'width': '100%'})
                                ])
                            ], style={'padding': '20px'})
                        ])
                    ])
                ])
            ], style={'width': '73%', 'marginLeft': '2%', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                      'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'margin': '20px'}),
        
        # Footer
        html.Div([
            html.Hr(),
            html.P("Global Franchise Map Dashboard demo © 2025", style={'textAlign': 'center'})
        ])
    ])
    
    # Define the callback outputs conditionally
    outputs = [
        Output('brand-table', 'data'),
        Output('brand-table', 'columns'),
        Output('country-chart', 'figure'),
        Output('product-chart', 'figure')
    ]
    
    if has_brand_origin and origin_options:
        outputs.append(Output('origin-chart', 'figure'))
        
    outputs.append(Output('stats-cards', 'children'))
    outputs.append(Output('world-map', 'figure'))
    outputs.append(Output('network-graph', 'figure'))
    outputs.append(Output('product-treemap', 'figure'))
    outputs.append(Output('group-concentration', 'figure'))
    outputs.append(Output('origin-host-analysis', 'figure'))
    
    # Define the callback inputs conditionally
    inputs = [Input('search-input', 'value')]
    
    if has_country and country_options:
        inputs.append(Input('country-filter', 'value'))
    else:
        inputs.append(Input('search-input', 'value'))
        
    if has_product_type and product_options:
        inputs.append(Input('product-filter', 'value'))
    else:
        inputs.append(Input('search-input', 'value'))
        
    if has_brand_origin and origin_options:
        inputs.append(Input('origin-filter', 'value'))
    else:
        inputs.append(Input('search-input', 'value'))
        
    if has_group_type and group_options:
        inputs.append(Input('group-type-filter', 'value'))
    else:
        inputs.append(Input('search-input', 'value'))

    @app.callback(outputs, inputs)
    def update_dashboard(search_term, selected_countries, selected_products, selected_origins, selected_group_types):
        # Handle the case when the inputs are actually duplicates of search_term
        if not has_country or not country_options:
            selected_countries = None
        if not has_product_type or not product_options:
            selected_products = None
        if not has_brand_origin or not origin_options:
            selected_origins = None
        if not has_group_type or not group_options:
            selected_group_types = None
            
        query = "SELECT * FROM brands"
        conditions = []
        
        # Build query conditions
        if search_term:
            conditions.append(f"brand_name LIKE '%{search_term}%'")
        if selected_countries:
            countries = ", ".join([f"'{c}'" for c in selected_countries])
            conditions.append(f"country IN ({countries})")
        if selected_products:
            products = ", ".join([f"'{p}'" for p in selected_products])
            conditions.append(f"product_type IN ({products})")
        if selected_origins:
            origins = ", ".join([f"'{o}'" for o in selected_origins])
            conditions.append(f"brand_origin IN ({origins})")
        if selected_group_types:
            group_types = ", ".join([f"'{g}'" for g in selected_group_types])
            conditions.append(f"group_type IN ({group_types})")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Get filtered data
        try:
            df = pd.read_sql(query, engine)
        except:
            # If query fails, get all data
            df = pd.read_sql("SELECT * FROM brands", engine)
        
        # Format table columns with human-readable names
        column_display_names = {
            'id': 'ID',
            'brand_name': 'Brand Name',
            'franchise_group': 'Franchise Group',
            'country': 'Country',
            'product_type': 'Product Type',
            'group_type': 'Group Type',
            'brand_origin': 'Brand Origin'
        }
        
        columns = [{"name": column_display_names.get(col, col.replace('_', ' ').title()), "id": col} for col in df.columns]
        data = df.to_dict('records')
        
        # Create country chart
        if len(df) > 0 and 'country' in df.columns:
            country_counts = df['country'].value_counts().reset_index()
            country_counts.columns = ['country', 'count']
            country_counts = country_counts.sort_values('count', ascending=False).head(10)
            
            country_fig = px.bar(
                country_counts,
                x='country', y='count', 
                color='count',
                color_continuous_scale='Blues',
                title='Top Countries by Brand Count'
            )
            country_fig.update_layout(
                xaxis_title="Country", 
                yaxis_title="Number of Brands",
                coloraxis_showscale=False
            )
        else:
            country_fig = px.bar(title='No Country Data Available')
            
        # Create world map - Enhancement 1
        if len(df) > 0 and 'country' in df.columns:
            # Get country counts for map
            country_counts_map = df['country'].value_counts().reset_index()
            country_counts_map.columns = ['country', 'count']
            
            # Create a world map
            world_map = go.Figure(data=go.Choropleth(
                locations=country_counts_map['country'],
                z=country_counts_map['count'],
                locationmode='ISO-3',  # country codes are ISO-3
                colorscale='Blues',
                colorbar_title="Number of Brands",
                text=country_counts_map['country'] + ': ' + country_counts_map['count'].astype(str) + ' brands',
                hoverinfo='text'
            ))
            
            world_map.update_layout(
                title_text='Global Brand Distribution',
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    projection_type='natural earth'
                )
            )
        else:
            world_map = go.Figure()
            world_map.update_layout(
                annotations=[{
                    'text': 'No Country Data Available',
                    'showarrow': False,
                    'font': {'size': 20},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
        
        # Create product type chart
        if len(df) > 0 and 'product_type' in df.columns and not df['product_type'].isna().all():
            product_counts = df['product_type'].value_counts().head(5)
            product_fig = px.pie(
                values=product_counts.values,
                names=product_counts.index,
                title='Top 5 Product Types',
                hole=0.4
            )
        else:
            product_fig = px.pie(title='No Product Type Data Available')
        
        # Create origin chart
        if has_brand_origin and origin_options and len(df) > 0 and 'brand_origin' in df.columns:
            # Filter out null values
            origin_df = df[df['brand_origin'].notna()]
            if len(origin_df) > 0:
                origin_counts = origin_df['brand_origin'].value_counts().head(10)
                origin_fig = px.bar(
                    x=origin_counts.index,
                    y=origin_counts.values,
                    title='Top 10 Brand Origins',
                    labels={'x': 'Origin Country', 'y': 'Number of Brands'},
                    color=origin_counts.values,
                    color_continuous_scale='Greens'
                )
            else:
                origin_fig = px.bar(title='No Brand Origin Data Available')
        else:
            origin_fig = px.bar(title='No Brand Origin Data Available')
        
        # Create stats cards
        stats_cards = [
            html.Div([
                html.H3(f"{len(df)}"),
                html.P("Total Brands")
            ], style={'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#007bff', 
                      'color': 'white', 'borderRadius': '5px', 'width': '30%'}),
            
            html.Div([
                html.H3(f"{df['country'].nunique() if 'country' in df.columns else 0}"),
                html.P("Countries")
            ], style={'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#28a745', 
                      'color': 'white', 'borderRadius': '5px', 'width': '30%'}),
            
            html.Div([
                html.H3(f"{df['franchise_group'].nunique() if 'franchise_group' in df.columns else 0}"),
                html.P("Franchise Groups")
            ], style={'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#dc3545', 
                      'color': 'white', 'borderRadius': '5px', 'width': '30%'})
        ]
        
        # Create network graph - Enhancement 3
        try:
            import networkx as nx
            
            if len(df) > 0 and 'franchise_group' in df.columns and 'brand_name' in df.columns:
                # Create a network graph using networkx
                G = nx.Graph()
                
                # Add franchise groups as nodes
                franchise_groups = df['franchise_group'].unique()
                for group in franchise_groups:
                    G.add_node(group, type='group', size=20)
                
                # Add brands as nodes and connect to franchise groups
                for _, row in df[['brand_name', 'franchise_group']].drop_duplicates().iterrows():
                    brand = row['brand_name']
                    group = row['franchise_group']
                    G.add_node(brand, type='brand', size=10)
                    G.add_edge(brand, group)
                
                # Use a layout algorithm to position nodes
                pos = nx.spring_layout(G, seed=42)  # Fixed seed for consistent layout
                
                # Create node traces
                node_x = []
                node_y = []
                node_sizes = []
                node_colors = []
                node_text = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    
                    # Different sizes and colors for brands vs groups
                    if G.nodes[node]['type'] == 'group':
                        node_sizes.append(25)
                        node_colors.append('#ff7f0e')  # Orange for franchise groups
                        node_text.append(f"Group: {node}")
                    else:
                        node_sizes.append(10)
                        node_colors.append('#1f77b4')  # Blue for brands
                        node_text.append(f"Brand: {node}")
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers',
                    hoverinfo='text',
                    text=node_text,
                    marker=dict(
                        size=node_sizes,
                        color=node_colors,
                        line=dict(width=1, color='#888')
                    )
                )
                
                # Create edge traces
                edge_x = []
                edge_y = []
                
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                )
                
                # Create the network graph
                network_fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Brand-Franchise Group Relationship Network',
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                            ))
                
                # Add a legend manually
                network_fig.add_trace(go.Scatter(
                    x=[None], y=[None], mode='markers',
                    marker=dict(size=15, color='#1f77b4'),
                    name='Brand'
                ))
                network_fig.add_trace(go.Scatter(
                    x=[None], y=[None], mode='markers',
                    marker=dict(size=15, color='#ff7f0e'),
                    name='Franchise Group'
                ))
                network_fig.update_layout(showlegend=True)
            else:
                network_fig = go.Figure()
                network_fig.update_layout(
                    annotations=[{
                        'text': 'No Relationship Data Available',
                        'showarrow': False,
                        'font': {'size': 20},
                        'xref': 'paper',
                        'yref': 'paper',
                        'x': 0.5,
                        'y': 0.5
                    }]
                )
        except ImportError:
            network_fig = go.Figure()
            network_fig.update_layout(
                annotations=[{
                    'text': 'NetworkX package required for this visualization',
                    'showarrow': False,
                    'font': {'size': 20},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
        
        # Create product category treemap - Enhancement 4-1
        if len(df) > 0 and 'product_type' in df.columns and not df['product_type'].isna().all():
            # Filter out null product types
            product_df = df[df['product_type'].notna()]
            
            if len(product_df) > 0:
                # Group by product type and count
                product_counts = product_df['product_type'].value_counts().reset_index()
                product_counts.columns = ['product_type', 'count']
                
                treemap_fig = px.treemap(
                    product_counts,
                    path=['product_type'],
                    values='count',
                    color='count',
                    color_continuous_scale='Blues',
                    title='Product Category Distribution'
                )
            else:
                treemap_fig = px.treemap(title='No Product Type Data Available')
        else:
            treemap_fig = px.treemap(title='No Product Type Data Available')
        
        # Create franchise group concentration analysis - Enhancement 4-2
        if len(df) > 0 and 'franchise_group' in df.columns:
            # Count brands per group and sort
            group_counts = df['franchise_group'].value_counts().reset_index()
            group_counts.columns = ['franchise_group', 'brand_count']
            group_counts = group_counts.sort_values('brand_count', ascending=False).head(15)
            
            # Create horizontal bar chart
            group_fig = px.bar(
                group_counts,
                y='franchise_group',
                x='brand_count',
                color='brand_count',
                orientation='h',
                title='Top 15 Franchise Groups by Brand Count',
                labels={'brand_count': 'Number of Brands', 'franchise_group': 'Franchise Group'},
                color_continuous_scale='Viridis'
            )
            
            group_fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                coloraxis_showscale=False
            )
        else:
            group_fig = px.bar(title='No Franchise Group Data Available')
        
        # Create origin vs host country analysis - Enhancement 4-3
        if len(df) > 0 and 'country' in df.columns and 'brand_origin' in df.columns:
            # Only include rows where both country and brand_origin are available
            origin_host_df = df[df['country'].notna() & df['brand_origin'].notna()]
            
            if len(origin_host_df) > 0:
                # Count brand presence by origin and host country
                origin_host_counts = origin_host_df.groupby(['brand_origin', 'country']).size().reset_index()
                origin_host_counts.columns = ['Origin', 'Host', 'Count']
                
                # Create heatmap
                origin_host_fig = px.density_heatmap(
                    origin_host_counts,
                    x='Host',
                    y='Origin',
                    z='Count',
                    title='Brand Distribution: Origin vs Host Countries',
                    labels={'Host': 'Host Country', 'Origin': 'Brand Origin', 'Count': 'Number of Brands'},
                    color_continuous_scale='YlGnBu'
                )
            else:
                origin_host_fig = px.density_heatmap(title='No Origin/Host Country Data Available')
        else:
            origin_host_fig = px.density_heatmap(title='No Origin/Host Country Data Available')
        
        # Return all results
        if has_brand_origin and origin_options:
            return (data, columns, country_fig, product_fig, origin_fig, stats_cards, world_map, 
                   network_fig, treemap_fig, group_fig, origin_host_fig)
        else:
            return (data, columns, country_fig, product_fig, stats_cards, world_map, 
                   network_fig, treemap_fig, group_fig, origin_host_fig)
    
    # CSV Export callback - Enhancement 2
    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("btn-export-csv", "n_clicks"),
        State('brand-table', 'data'),
        prevent_initial_call=True,
    )
    def export_dataframe_to_csv(n_clicks, table_data):
        """Export the currently filtered data to CSV"""
        if n_clicks:
            # Convert the filtered data to a DataFrame
            export_df = pd.DataFrame(table_data)
            return dcc.send_data_frame(export_df.to_csv, "gfm_export.csv", index=False)
        return None
        
    return app

# ----------------------
# 4. Execution Script
# ----------------------
if __name__ == '__main__':
    import os
    
    # Install required packages for enhanced features
    try:
        import networkx
    except ImportError:
        print("Installing networkx for network graph visualization...")
        import subprocess
        subprocess.call(['pip', 'install', 'networkx'])
        try:
            import networkx
        except ImportError:
            print("Warning: Could not install networkx. Network visualization will be limited.")
    
    # Point to your GFM dataset - update with the correct path if needed
    data_file = 'GFM Dataset (1).xlsx'
    
    # Check if data file exists in current directory, if not check in downloads folder
    if not os.path.exists(data_file):
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', data_file)
        if os.path.exists(downloads_path):
            data_file = downloads_path
        else:
            rhv_data_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'rhv_data', data_file)
            if os.path.exists(rhv_data_path):
                data_file = rhv_data_path
            else:
                print(f"Error: Data file '{data_file}' not found in current directory or Downloads folder.")
                print("Please make sure the file exists and is named correctly.")
                exit(1)
    
    print(f"Loading data from: {data_file}")
    
    # Make sure pandas has openpyxl for Excel reading
    try:
        import openpyxl
    except ImportError:
        print("Installing openpyxl for Excel support...")
        import subprocess
        subprocess.call(['pip', 'install', 'openpyxl'])
    
    # 1. Load and clean data
    print("Loading and cleaning data...")
    df = load_and_clean_data(data_file)
    
    # 2. Setup database
    print("Setting up database...")
    engine = setup_database()
    update_database(engine, df)
    
    # 3. Start dashboard
    print("Starting dashboard at http://127.0.0.1:8050/")
    app = create_dashboard(engine)
    
    # Use try/except to handle different versions of Dash
    
        # Fallback to app.run if run_server is truly deprecated in your version
    app.run(debug=True, port=8050)