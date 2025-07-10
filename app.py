import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

def load_file(uploaded_file):
    """Load a file based on its extension"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            return pd.read_csv(uploaded_file)
        elif file_extension in ['xls', 'xlsx']:
            # For Excel files, we'll read the first sheet by default
            # You could modify this to handle multiple sheets if needed
            return pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        raise Exception(f"Error reading file {uploaded_file.name}: {str(e)}")

def find_common_columns(dataframes):
    """Find columns that exist in all dataframes"""
    if not dataframes:
        return []
    
    # Start with columns from first dataframe
    common_cols = set(dataframes[0].columns)
    
    # Find intersection with all other dataframes
    for df in dataframes[1:]:
        common_cols = common_cols.intersection(set(df.columns))
    
    return sorted(list(common_cols))

def convert_to_float(df, columns):
    """Convert specified columns to float, handling errors gracefully"""
    df_converted = df.copy()
    
    for col in columns:
        try:
            # Try to convert to numeric, coerce errors to NaN
            df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
        except Exception as e:
            st.warning(f"Could not convert column '{col}' to float: {e}")
    
    return df_converted

def create_spider_chart(dataframes, selected_columns, file_names):
    """Create a spider chart from multiple datasets"""
    fig = go.Figure()
    
    # Define colors for different datasets
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    for i, (df, name) in enumerate(zip(dataframes, file_names)):
        # Calculate mean values for each selected column
        values = []
        for col in selected_columns:
            if col in df.columns:
                # Calculate mean, ignoring NaN values
                mean_val = df[col].mean()
                values.append(mean_val if not pd.isna(mean_val) else 0)
            else:
                values.append(0)
        
        # Close the radar chart by adding the first value at the end
        values += [values[0]]
        theta = selected_columns + [selected_columns[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=theta,
            fill='toself',
            name=name,
            line_color=colors[i % len(colors)],
            opacity=0.7
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max([df[selected_columns].max().max() for df in dataframes if not df.empty]) * 1.1]
            )
        ),
        showlegend=True,
        title="Spider Chart Comparison",
        height=600
    )
    
    return fig

def main():
    st.set_page_config(page_title="Multi-Dataset Spider Chart", page_icon="🕷️", layout="wide")
    
    st.title("Multi-Dataset Spider Chart Generator")
    st.markdown("Upload multiple datasets and create comparative spider charts based on common columns.")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['csv', 'xls', 'xlsx'],
        accept_multiple_files=True,
        help="Upload 1 or more CSV or Excel files to compare"
    )
    
    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} file(s)")
        
        # Load all datasets
        dataframes = []
        file_names = []
        
        for uploaded_file in uploaded_files:
            try:
                # Load file based on extension
                df = load_file(uploaded_file)
                dataframes.append(df)
                file_names.append(uploaded_file.name)
                
                # Show basic info about each file
                with st.expander(f"Preview: {uploaded_file.name}"):
                    st.write(f"Shape: {df.shape}")
                    st.write("First few rows:")
                    st.dataframe(df.head())
                    
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
        
        if dataframes:
            # Find common columns
            common_columns = find_common_columns(dataframes)
            
            if common_columns:
                st.subheader("📊 Column Selection")
                st.write("The following are all the columns that exist in all of your datasets. Select the ones that contain results/scores that you'd like to include in the spider chart.")
                st.write(f"Found {len(common_columns)} common columns across all datasets:")
                
                # Display common columns
                st.write(", ".join(common_columns))
                
                # Let user select which columns to use for spider chart
                selected_columns = st.multiselect(
                    "Select columns for spider chart:",
                    options=common_columns,
                    default=common_columns[:min(0, len(common_columns))],  # Default to first 6 columns
                    help="Choose the columns you want to visualize in the spider chart"
                )
                
                if selected_columns:
                    # Convert selected columns to float
                    converted_dataframes = []
                    
                    for df in dataframes:
                        converted_df = convert_to_float(df, selected_columns)
                        converted_dataframes.append(converted_df)
                    
                    # Show conversion summary
                    st.subheader("🔄 Data Conversion Summary")
                    
                    for i, (df, name) in enumerate(zip(converted_dataframes, file_names)):
                        with st.expander(f"Conversion details for {name}"):
                            for col in selected_columns:
                                non_null_count = df[col].notna().sum()
                                total_count = len(df)
                                mean_val = df[col].mean()
                                
                                st.write(f"**{col}**: {non_null_count}/{total_count} valid values, Mean: {mean_val:.2f}")
                    
                    # Create and display spider chart
                    st.subheader("🕸️ Spider Chart")
                    
                    fig = create_spider_chart(converted_dataframes, selected_columns, file_names)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show summary statistics
                    st.subheader("📈 Summary Statistics")
                    
                    summary_data = []
                    for df, name in zip(converted_dataframes, file_names):
                        row = {"Dataset": name}
                        for col in selected_columns:
                            row[f"{col}_mean"] = df[col].mean()
                        summary_data.append(row)
                    
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df)
                    
                else:
                    st.info("Please select at least one column to create the spider chart.")
            
            else:
                st.warning("No common columns found across all datasets. Please ensure your files have overlapping column names.")
    
    else:
        st.info("Please upload one or more CSV or Excel files to get started.")
        
        # Show example of expected data format
        st.subheader("📋 Expected Data Format")
        st.write("Your files should have:")
        st.write("• **Supported formats**: CSV (.csv), Excel (.xls, .xlsx)")
        st.write("• Common column names across all files")
        st.write("• Numeric data that can be converted to floats")
        st.write("• Headers in the first row")
        st.write("• For Excel files: data will be read from the first sheet")
        
        # Example data
        example_data = {
            "Category": ["A", "B", "C"],
            "Score1": [85, 92, 78],
            "Score2": [90, 88, 95],
            "Rating": [4.2, 4.5, 3.8]
        }
        
        st.write("Example data structure:")
        st.dataframe(pd.DataFrame(example_data))

if __name__ == "__main__":
    main()
