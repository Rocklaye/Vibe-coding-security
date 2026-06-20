export type User = {
  id: number;
  name: string;
  jobTitle?: string;
  company?: string;
  skills?: string;
};

export type Post = {
  id: number;
  content: string;
  authorName: string;
  authorJob: string;
  created_at: string;
  likesCount: number;
  commentsCount: number;
};

export type Connection = {
  id: number;
  name: string;
  jobTitle: string;
  status: 'pending' | 'accepted';
  requesterId: number;
};

export type Message = {
  id: number;
  sender_id: number;
  receiver_id: number;
  content: string;
  created_at: string;
};

export type Notification = {
  id: number;
  content: string;
  is_read: number;
  created_at: string;
};
