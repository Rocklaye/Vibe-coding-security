import { useState, useEffect } from 'react';
import { Post } from '../types';
import { ThumbsUp, MessageSquare, Send } from 'lucide-react';

export function Feed({ token }: { token: string }) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState('');
  const [activeComments, setActiveComments] = useState<number | null>(null);
  const [comments, setComments] = useState<{content: string, name: string}[]>([]);
  const [newComment, setNewComment] = useState('');

  const fetchPosts = async () => {
    const res = await fetch('/api/posts', { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) setPosts(await res.json());
  };

  useEffect(() => {
    fetchPosts();
  }, [token]);

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ content: newPost })
    });
    setNewPost('');
    fetchPosts();
  };

  const handleLike = async (postId: number) => {
    await fetch(`/api/posts/${postId}/like`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    fetchPosts();
  };

  const loadComments = async (postId: number) => {
    if (activeComments === postId) {
      setActiveComments(null);
      return;
    }
    const res = await fetch(`/api/posts/${postId}/comments`, { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) {
      setComments(await res.json());
      setActiveComments(postId);
    }
  };

  const handleAddComment = async (e: React.FormEvent, postId: number) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    await fetch(`/api/posts/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ content: newComment })
    });
    setNewComment('');
    loadComments(postId); // reload
    fetchPosts(); // to update count
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleCreatePost}>
          <textarea
            value={newPost}
            onChange={(e) => setNewPost(e.target.value)}
            className="w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:border-blue-500 mb-3"
            placeholder="De quoi voulez-vous discuter avec votre réseau ?"
            rows={3}
          />
          <div className="flex justify-end">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700">
              Publier
            </button>
          </div>
        </form>
      </div>

      <div className="space-y-6">
        {posts.map(post => (
          <div key={post.id} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b border-gray-100">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold mr-3">
                  {post.authorName.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{post.authorName}</h3>
                  <p className="text-xs text-gray-500">{post.authorJob}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{new Date(post.created_at).toLocaleString()}</p>
                </div>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap">{post.content}</p>
            </div>
            
            <div className="px-4 py-2 flex items-center text-sm text-gray-500 border-b border-gray-100">
              <span className="mr-4">{post.likesCount} J'aime</span>
              <span>{post.commentsCount} Commentaires</span>
            </div>

            <div className="flex items-center p-2">
              <button onClick={() => handleLike(post.id)} className="flex items-center justify-center w-1/2 py-2 text-gray-600 hover:bg-gray-50 rounded">
                <ThumbsUp size={18} className="mr-2" /> J'aime
              </button>
              <button onClick={() => loadComments(post.id)} className="flex items-center justify-center w-1/2 py-2 text-gray-600 hover:bg-gray-50 rounded">
                <MessageSquare size={18} className="mr-2" /> Commenter
              </button>
            </div>

            {activeComments === post.id && (
              <div className="bg-gray-50 p-4 border-t border-gray-200">
                <div className="space-y-4 mb-4">
                  {comments.map((comment, idx) => (
                     <div key={idx} className="flex">
                       <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-xs font-bold mr-2 flex-shrink-0">
                         {comment.name.charAt(0)}
                       </div>
                       <div className="bg-white p-2 rounded-lg border border-gray-200 text-sm">
                         <span className="font-semibold block">{comment.name}</span>
                         {comment.content}
                       </div>
                     </div>
                  ))}
                  {comments.length === 0 && <p className="text-sm text-gray-500 italic">Soyez le premier à commenter.</p>}
                </div>
                
                <form onSubmit={(e) => handleAddComment(e, post.id)} className="flex">
                  <input 
                    type="text" 
                    value={newComment} 
                    onChange={e => setNewComment(e.target.value)} 
                    placeholder="Ajouter un commentaire..." 
                    className="flex-grow rounded-l-lg border border-gray-300 p-2 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <button type="submit" className="bg-blue-600 text-white p-2 rounded-r-lg hover:bg-blue-700">
                    <Send size={18} />
                  </button>
                </form>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
