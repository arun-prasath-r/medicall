import React from 'react';
import { VoiceAssistant } from '../components/ai/VoiceAssistant';

export const VoiceAssistantPage = () => {
  return (
    <div className="page-wrapper" style={{ padding: '1.5rem 0' }}>
      <div className="container">
        <VoiceAssistant />
      </div>
    </div>
  );
};

export default VoiceAssistantPage;

