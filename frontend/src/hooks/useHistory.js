import { useState, useEffect } from 'react';
import { api } from '../services/api.js';

export const useHistory = () => {
  const [history, setHistory] = useState([]);

  const loadHistory = async () => {
    try {
      const data = await api.getHistory();
      setHistory(data.history || []);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return { history, loadHistory };
};