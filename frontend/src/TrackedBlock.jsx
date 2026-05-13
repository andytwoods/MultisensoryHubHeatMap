import React from 'react';

const TrackedBlock = ({ blockId, topic, concept, contentType, label, children }) => {
  if (process.env.NODE_ENV === 'development' && !blockId) {
    console.warn("TrackedBlock missing blockId");
  }

  return (
    <div 
      data-block-id={blockId} 
      data-topic={topic} 
      data-concept={concept} 
      data-content-type={contentType}
      data-label={label}
    >
      {children}
    </div>
  );
};

export default TrackedBlock;
