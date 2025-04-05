import os
import pandas as pd

from datetime import datetime, timedelta

class YouTubeAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Keyword Analyzer")
        self.root.geometry("1200x800")
        self.api_key = StringVar()
        self.keyword = StringVar()
        self.time_range = StringVar(value="6h")  # Default to 6 hours
        self.results = []
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Settings tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # API Key
        ttk.Label(settings_frame, text="AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9Il").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        ttk.Entry(settings_frame, textvariable=self.api_key, width=50).grid(row=0, column=1, padx=10, pady=10, sticky=W)
        
        # Keywords frame
        keyword_frame = ttk.LabelFrame(settings_frame, text="Keywords")
        keyword_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=W+E)
        
        ttk.Label(keyword_frame, text="Keyword:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        ttk.Entry(keyword_frame, textvariable=self.keyword, width=30).grid(row=0, column=1, padx=10, pady=10, sticky=W)
        
        # Listbox for keywords
        self.keyword_list = Listbox(keyword_frame, width=50, height=10)
        self.keyword_list.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=W+E)
        
        keyword_buttons_frame = ttk.Frame(keyword_frame)
        keyword_buttons_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        
        ttk.Button(keyword_buttons_frame, text="Add Keyword", command=self.add_keyword).pack(side=LEFT, padx=5)
        ttk.Button(keyword_buttons_frame, text="Remove Keyword", command=self.remove_keyword).pack(side=LEFT, padx=5)
        ttk.Button(keyword_buttons_frame, text="Export Keywords", command=self.export_keywords).pack(side=LEFT, padx=5)
        ttk.Button(keyword_buttons_frame, text="Import Keywords", command=self.import_keywords).pack(side=LEFT, padx=5)
        
        # Time range frame
        time_frame = ttk.LabelFrame(settings_frame, text="Time Range")
        time_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky=W+E)
        
        ttk.Label(time_frame, text="Time Range:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        time_options = ["1h", "6h", "12h", "24h", "48h", "7d", "30d"]
        ttk.Combobox(time_frame, textvariable=self.time_range, values=time_options).grid(row=0, column=1, padx=10, pady=10, sticky=W)
        
        # Analysis button
        ttk.Button(settings_frame, text="Run Analysis", command=self.run_analysis).grid(row=3, column=0, columnspan=2, padx=10, pady=20)
        
        # Results tab
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results")
        
        # Create frame for table
        table_frame = ttk.LabelFrame(results_frame, text="Videos Found")
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for results
        columns = ("Title", "Channel", "Published", "Views", "Keywords")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Set column headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)
            
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Export results button
        ttk.Button(table_frame, text="Export Results", command=self.export_results).pack(padx=10, pady=10)
        
        # Graph frame
        graph_frame = ttk.LabelFrame(results_frame, text="Keyword Frequency")
        graph_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    
    def add_keyword(self):
        if self.keyword.get():
            self.keyword_list.insert(END, self.keyword.get())
            self.keyword.set("")
    
    def remove_keyword(self):
        selected = self.keyword_list.curselection()
        if selected:
            self.keyword_list.delete(selected)
    
    def export_keywords(self):
        keywords = self.keyword_list.get(0, END)
        if keywords:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(list(keywords), f)
    
    def import_keywords(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    keywords = json.load(f)
                    self.keyword_list.delete(0, END)
                    for keyword in keywords:
                        self.keyword_list.insert(END, keyword)
            except Exception as e:
                print(f"Error importing keywords: {e}")
    
    def get_time_filter(self):
        time_val = self.time_range.get()
        now = datetime.now()
        
        if time_val.endswith('h'):
            hours = int(time_val[:-1])
            published_after = now - timedelta(hours=hours)
        elif time_val.endswith('d'):
            days = int(time_val[:-1])
            published_after = now - timedelta(days=days)
        else:
            # Default to 6 hours
            published_after = now - timedelta(hours=6)
            
        # Format for YouTube API
        return published_after.isoformat() + "Z"
    
    def run_analysis(self):
        if not self.api_key.get():
            print("Please enter a YouTube API key")
            return
            
        keywords = list(self.keyword_list.get(0, END))
        if not keywords:
            print("Please add at least one keyword")
            return
            
        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.results = []
        
        try:
            youtube = build("youtube", "v3", developerKey=self.api_key.get())
            
            keyword_counts = {}
            
            for keyword in keywords:
                # Set up request
                published_after = self.get_time_filter()
                
                request = youtube.search().list(
                    part="snippet",
                    maxResults=50,
                    q=keyword,
                    type="video",
                    publishedAfter=published_after,
                    order="relevance"
                )
                response = request.execute()
                
                # Count keyword frequency
                video_count = len(response.get("items", []))
                keyword_counts[keyword] = video_count
                
                # Process results
                for item in response.get("items", []):
                    video_id = item["id"]["videoId"]
                    
                    # Get video details
                    video_request = youtube.videos().list(
                        part="statistics,snippet",
                        id=video_id
                    )
                    video_response = video_request.execute()
                    
                    if video_response["items"]:
                        video_data = video_response["items"][0]
                        
                        title = video_data["snippet"]["title"]
                        channel = video_data["snippet"]["channelTitle"]
                        published = video_data["snippet"]["publishedAt"]
                        views = video_data["statistics"].get("viewCount", "0")
                        
                        # Extract date part for display
                        pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                        pub_formatted = pub_date.strftime("%Y-%m-%d %H:%M")
                        
                        # Add to results
                        self.tree.insert("", END, values=(title, channel, pub_formatted, views, keyword))
                        
                        self.results.append({
                            "title": title,
                            "channel": channel,
                            "published": published,
                            "views": views,
                            "keyword": keyword
                        })
            
            # Update graph
            self.update_graph(keyword_counts)
            
        except Exception as e:
            print(f"Error: {e}")
    
    def update_graph(self, keyword_counts):
        self.ax.clear()
        
        keywords = list(keyword_counts.keys())
        counts = list(keyword_counts.values())
        
        bars = self.ax.bar(keywords, counts, color='skyblue')
        
        # Add labels
        self.ax.set_xlabel('Keywords')
        self.ax.set_ylabel('Number of Videos')
        self.ax.set_title('Keyword Frequency in YouTube Videos')
        
        # Add text labels on bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom')
        
        self.ax.set_xticklabels(keywords, rotation=45, ha='right')
        self.fig.tight_layout()
        self.canvas.draw()
    
    def export_results(self):
        if not self.results:
            print("No results to export")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                              filetypes=[("CSV files", "*.csv"), 
                                                         ("Excel files", "*.xlsx")])
        if not file_path:
            return
            
        df = pd.DataFrame(self.results)
        
        if file_path.endswith('.csv'):
            df.to_csv(file_path, index=False)
        elif file_path.endswith('.xlsx'):
            df.to_excel(file_path, index=False)
        
        print(f"Results exported to {file_path}")

if __name__ == "__main__":
    root = Tk()
    app = YouTubeAnalyzer(root)
    root.mainloop()
