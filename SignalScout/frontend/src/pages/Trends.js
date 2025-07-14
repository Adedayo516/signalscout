import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  TrendingUp, 
  RefreshCw, 
  ExternalLink,
  MessageCircle,
  Heart,
  Eye,
  Calendar,
  Tag
} from 'lucide-react';
import { fetchRedditTrends, fetchYouTubeTrends, getTrends } from '../services/api';
import toast from 'react-hot-toast';

const Trends = () => {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    platform: 'all',
    topic: 'all',
    sortBy: 'virality_score'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [subredditInput, setSubredditInput] = useState('technology');

  useEffect(() => {
    loadTrends();
  }, [filters]);

  const loadTrends = async () => {
    try {
      setLoading(true);
      const platform = filters.platform === 'all' ? null : filters.platform;
      const data = await getTrends(100, platform);
      setTrends(data.trends || []);
    } catch (error) {
      toast.error('Failed to load trends');
      console.error('Error loading trends:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNewRedditTrends = async () => {
    try {
      setLoading(true);
      toast.loading('Fetching Reddit trends...');
      await fetchRedditTrends(subredditInput, 25);
      toast.dismiss();
      toast.success(`Fetching trends from r/${subredditInput}`);
      // Reload trends after a short delay
      setTimeout(loadTrends, 2000);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to fetch Reddit trends');
    } finally {
      setLoading(false);
    }
  };

  const fetchNewYouTubeTrends = async () => {
    try {
      setLoading(true);
      toast.loading('Fetching YouTube trends...');
      await fetchYouTubeTrends();
      toast.dismiss();
      toast.success('Fetching YouTube trends');
      // Reload trends after a short delay
      setTimeout(loadTrends, 2000);
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to fetch YouTube trends');
    } finally {
      setLoading(false);
    }
  };

  const filteredTrends = trends.filter(trend => {
    const matchesSearch = trend.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trend.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTopicFilter = filters.topic === 'all' || trend.topic_cluster === filters.topic;
    
    return matchesSearch && matchesTopicFilter;
  }).sort((a, b) => {
    switch (filters.sortBy) {
      case 'virality_score':
        return b.virality_score - a.virality_score;
      case 'engagement_rate':
        return b.engagement_rate - a.engagement_rate;
      case 'score':
        return b.score - a.score;
      case 'created_at':
        return new Date(b.created_at) - new Date(a.created_at);
      default:
        return 0;
    }
  });

  const getUniqueTopics = () => {
    const topics = [...new Set(trends.map(trend => trend.topic_cluster))];
    return topics.filter(topic => topic);
  };

  const getViralityColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600 bg-green-100';
      case 'negative': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const TrendCard = ({ trend }) => (
    <div className="card hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
            trend.platform === 'reddit' ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800'
          }`}>
            {trend.platform}
          </span>
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getSentimentColor(trend.sentiment)}`}>
            {trend.sentiment}
          </span>
        </div>
        <div className={`px-2.5 py-1 rounded-full text-xs font-medium ${getViralityColor(trend.virality_score)}`}>
          Viral Score: {trend.virality_score?.toFixed(1)}
        </div>
      </div>

      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
        {trend.title}
      </h3>

      {trend.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {trend.description}
        </p>
      )}

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <Eye className="w-4 h-4" />
            <span>{trend.score?.toLocaleString()}</span>
          </div>
          <div className="flex items-center space-x-1">
            <MessageCircle className="w-4 h-4" />
            <span>{trend.comments_count}</span>
          </div>
          <div className="flex items-center space-x-1">
            <TrendingUp className="w-4 h-4" />
            <span>{trend.engagement_rate?.toFixed(1)}%</span>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Calendar className="w-4 h-4" />
          <span>{formatDate(trend.created_at)}</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Tag className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-600">{trend.topic_cluster}</span>
          <span className="text-sm text-gray-400">by {trend.author}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <a
            href={trend.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            View
          </a>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trending Content</h1>
          <p className="text-gray-600 mt-1">Discover viral content across platforms</p>
        </div>
        <button
          onClick={loadTrends}
          disabled={loading}
          className="btn-primary flex items-center space-x-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Fetch New Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fetch Reddit Trends</h3>
          <div className="flex space-x-3">
            <input
              type="text"
              value={subredditInput}
              onChange={(e) => setSubredditInput(e.target.value)}
              placeholder="Enter subreddit name"
              className="input-field flex-1"
            />
            <button
              onClick={fetchNewRedditTrends}
              disabled={loading}
              className="btn-primary whitespace-nowrap"
            >
              Fetch Reddit
            </button>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fetch YouTube Trends</h3>
          <button
            onClick={fetchNewYouTubeTrends}
            disabled={loading}
            className="btn-primary w-full"
          >
            Fetch YouTube Trending
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search trends..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field"
            />
          </div>

          <select
            value={filters.platform}
            onChange={(e) => setFilters({ ...filters, platform: e.target.value })}
            className="input-field"
          >
            <option value="all">All Platforms</option>
            <option value="reddit">Reddit</option>
            <option value="youtube">YouTube</option>
          </select>

          <select
            value={filters.topic}
            onChange={(e) => setFilters({ ...filters, topic: e.target.value })}
            className="input-field"
          >
            <option value="all">All Topics</option>
            {getUniqueTopics().map(topic => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>

          <select
            value={filters.sortBy}
            onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
            className="input-field"
          >
            <option value="virality_score">Virality Score</option>
            <option value="engagement_rate">Engagement Rate</option>
            <option value="score">Score/Views</option>
            <option value="created_at">Date</option>
          </select>
        </div>
      </div>

      {/* Trends Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading trends...</span>
        </div>
      ) : filteredTrends.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredTrends.map((trend) => (
            <TrendCard key={trend.id} trend={trend} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No trends found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {trends.length === 0 
              ? "Start by fetching trends from Reddit or YouTube" 
              : "Try adjusting your search or filters"
            }
          </p>
        </div>
      )}

      {/* Stats */}
      {trends.length > 0 && (
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{trends.length}</p>
              <p className="text-sm text-gray-500">Total Trends</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {filteredTrends.filter(t => t.virality_score >= 70).length}
              </p>
              <p className="text-sm text-gray-500">Viral Content</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {(filteredTrends.reduce((sum, t) => sum + t.virality_score, 0) / filteredTrends.length || 0).toFixed(1)}
              </p>
              <p className="text-sm text-gray-500">Avg Virality</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{getUniqueTopics().length}</p>
              <p className="text-sm text-gray-500">Topics</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trends;