import React from 'react';

interface TodoItem {
  id: string;
  content: string;
  status: 'completed' | 'in_progress' | 'pending';
}

interface TodoListProps {
  todos: TodoItem[];
  isUpdate?: boolean;
}

const TodoList: React.FC<TodoListProps> = ({ todos, isUpdate = false }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'in_progress':
        return (
          <div className="w-5 h-5 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0">
            <div className="w-2 h-2 bg-white rounded-full"></div>
          </div>
        );
      case 'pending':
      default:
        return (
          <div className="w-5 h-5 rounded-full border-2 border-gray-400 flex-shrink-0"></div>
        );
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'in_progress':
        return 'In Progress';
      case 'pending':
      default:
        return 'Pending';
    }
  };

  const completedCount = todos.filter(todo => todo.status === 'completed').length;
  const inProgressCount = todos.filter(todo => todo.status === 'in_progress').length;
  const pendingCount = todos.filter(todo => todo.status === 'pending').length;

  return (
    <div className="mb-3">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-5 h-5 rounded-md bg-orange-500 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <h3 className="text-gray-900 dark:text-white font-bold text-sm">
          {isUpdate ? 'Updating todo list' : 'Creating todo list'}
        </h3>
      </div>

      {/* Todo Items */}
      <div className="space-y-1 ml-8">
        {todos.map((todo) => (
          <div key={todo.id} className="bg-gray-100 dark:bg-gray-800/80 rounded-lg p-1.5 flex items-start gap-2">
            {getStatusIcon(todo.status)}
            <div className="flex-1 min-w-0">
              <div className={`text-gray-900 dark:text-white text-xs leading-relaxed ${todo.status === 'completed' ? 'line-through opacity-60' : ''}`}>
                {todo.content}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TodoList;
