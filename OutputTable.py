import pandas as pd

# Read the CSV file
csv_file = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/24_25_combined_gw3_data.csv'
data = pd.read_csv(csv_file)

# Generate HTML table
html_table = data.to_html(index=False)

# HTML template
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Fantasy Premier League - GW3 Data</title>
    <style>
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        table, th, td {{
            border: 1px solid black;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <h1>Fantasy Premier League - GW3 Data</h1>
    {html_table}
</body>
</html>
"""

# Save the HTML content to a file
output_file = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/index.html'
with open(output_file, 'w') as file:
    file.write(html_content)

print(f"HTML file generated: {output_file}")
