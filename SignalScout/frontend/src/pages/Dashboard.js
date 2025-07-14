import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  Sparkles, 
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Zap
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getViralityAnalytics, getTrends, healthCheck } from '../services/api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [recentTrends, setRecentTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    loadDashboardData();
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      await healthCheck();
      setApiStatus('connected');
    } catch (error) {
      setApiStatus('error');
      toast.error('Backend API is not connected');
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load analytics and trends in parallel
      const [analyticsData, trendsData] = await Promise.all([
        getViralityAnalytics(7),
        getTrends(10)
      ]);
      
      setAnalytics(analyticsData.analytics || analyticsData);
      setRecentTrends(trendsData.trends || []);
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const mockEngagementData = [
    { name: 'Mon', value: 65 },
    { name: 'Tue', value: 78 },
    { name: 'Wed', value: 82 },
    { name: 'Thu', value: 95 },
    { name: 'Fri', value: 88 },
    { name: 'Sat', value: 92 },
    { name: 'Sun', value: 76 },
  ];

  const StatCard = ({ title, value, change, icon: Icon, color = "blue" }) => {
    const isPositive = change > 0;
    
    return (
      <div className="metric-card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <div className={`flex items-center mt-1 text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
              <span className="ml-1">{Math.abs(change)}%</span>
              <span className="text-gray-500 ml-1">from last week</span>
            </div>
          </div>
          <div className={`p-3 rounded-full bg-${color}-100`}>
            <Icon className={`w-6 h-6 text-${color}-600`} />
          </div>
        </div>
      </div>
    );
  };

  const ApiStatusBadge = () => {
    const statusConfig = {
      checking: { color: 'yellow', text: 'Checking...', icon: Activity },
      connected: { color: 'green', text: 'API Connected', icon: Zap },
      error: { color: 'red', text: 'API Offline', icon: Activity }
    };
    
    const config = statusConfig[apiStatus];
    const Icon = config.icon;
    
    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${config.color}-100 text-${config.color}-800`}>
        <Icon className="w-4 h-4 mr-2" />
        {config.text}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor trends and content performance</p>
        </div>
        <ApiStatusBadge />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Content Analyzed"
          value={analytics?.total_content || 0}
          change={12}
          icon={BarChart3}
          color="blue"
        />
        <StatCard
          title="Viral Content Found"
          value={analytics?.viral_content_count || 0}
          change={8}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Avg Virality Score"
          value={analytics?.avg_virality_score?.toFixed(1) || '0.0'}
          change={-3}
          icon={Sparkles}
          color="purple"
        />
        <StatCard
          title="Active Platforms"
          value={Object.keys(analytics?.platform_breakdown || {}).length}
          change={0}
          icon={Users}
          color="orange"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Engagement Trend Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockEngagementData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={3}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Performance */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(analytics?.platform_breakdown || {}).map(([platform, count]) => ({ platform, count }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="platform" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Trends */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Recent Viral Trends</h3>
          <button 
            onClick={loadDashboardData}
            className="btn-primary text-sm"
          >
            Refresh Data
          </button>
        </div>
        
        {recentTrends.length > 0 ? (
          <div className="space-y-4">
            {recentTrends.slice(0, 5).map((trend, index) => (
              <div key={trend.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                      {trend.platform}
                    </span>
                    <span className="text-sm text-gray-500">
                      {trend.topic_cluster}
                    </span>
                  </div>
                  <h4 className="font-medium text-gray-900 mt-1 line-clamp-2">
                    {trend.title}
                  </h4>
                  <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                    <span>Score: {trend.score?.toLocaleString()}</span>
                    <span>Engagement: {trend.engagement_rate?.toFixed(1)}%</span>
                    <span className="font-medium text-primary-600">
                      Virality: {trend.virality_score?.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      trend.virality_score > 80 ? 'bg-green-400' :
                      trend.virality_score > 60 ? 'bg-yellow-400' : 'bg-gray-400'
                    }`}></div>
                    <span className="text-sm font-medium text-gray-900">
                      #{index + 1}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No trends yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start by fetching trends from Reddit or YouTube to see viral content here.
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <TrendingUp className="mx-auto h-12 w-12 text-primary-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Fetch New Trends</h3>
            <p className="text-sm text-gray-500 mt-2">
              Discover trending content from Reddit and YouTube
            </p>
          </div>
        </div>
        
        <div className="card hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <Sparkles className="mx-auto h-12 w-12 text-purple-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Generate Content</h3>
            <p className="text-sm text-gray-500 mt-2">
              Create original posts inspired by viral trends
            </p>
          </div>
        </div>
        
        <div className="card hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-green-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">View Analytics</h3>
            <p className="text-sm text-gray-500 mt-2">
              Analyze performance patterns and insights
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;