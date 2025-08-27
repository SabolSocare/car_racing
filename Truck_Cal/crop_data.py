#!/usr/bin/env python3
import pandas as pd
import os
from datetime import datetime

def crop_csv_data(input_file, output_file, start_time, end_time):
    """
    Crop CSV data between start_time and end_time
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Convert timeStamp column to datetime
        df['timeStamp'] = pd.to_datetime(df['timeStamp'])
        
        # Filter data between start and end time
        mask = (df['timeStamp'] >= start_time) & (df['timeStamp'] <= end_time)
        filtered_df = df.loc[mask]
        
        # Save the filtered data
        filtered_df.to_csv(output_file, index=False)
        
        print(f"Processed {input_file}: {len(filtered_df)} rows extracted")
        return len(filtered_df)
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return 0

def main():
    # Define time range
    start_time = "2025-06-07T13:44:00"
    end_time = "2025-06-07T14:14:16"
    
    # Convert to datetime objects
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time)
    
    # Input and output directories
    input_dir = "/Users/socaresabol/POC/test/F1/Truck_Cal"
    output_dir = "/Users/socaresabol/POC/test/F1/Truck_Cal/cropped_data"
    
    # List all CSV files in the input directory
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv') and 'truck' in f]
    
    print(f"Found {len(csv_files)} CSV files to process")
    print(f"Time range: {start_time} to {end_time}")
    print("-" * 50)
    
    total_rows = 0
    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        
        # Create output filename with cropped prefix
        output_filename = f"cropped_{csv_file}"
        output_path = os.path.join(output_dir, output_filename)
        
        rows_extracted = crop_csv_data(input_path, output_path, start_dt, end_dt)
        total_rows += rows_extracted
    
    print("-" * 50)
    print(f"Processing complete! Total rows extracted: {total_rows}")
    print(f"Output files saved in: {output_dir}")

if __name__ == "__main__":
    main()
