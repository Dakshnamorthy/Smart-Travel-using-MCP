import React from 'react';

const SavedTrips = ({ trips, onDelete }) => {
  return (
    <div style={{ flex: 1, backgroundColor: 'var(--color-bg-panel)', overflowY: 'auto', padding: '20px' }}>
      <h2 style={{ marginBottom: '20px', color: 'var(--color-primary-dark)' }}>My Saved Trips ✈️</h2>
      
      {trips.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          You haven't saved any trips yet. <br/>
          Plan a trip in the chat and click the "Save Trip" button!
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {trips.map(trip => (
            <div key={trip.id} style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '16px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-divider)', paddingBottom: '8px', marginBottom: '8px' }}>
                <strong style={{ color: 'var(--color-text-secondary)' }}>Saved on: {trip.date}</strong>
                <button 
                  onClick={() => onDelete(trip.id)}
                  style={{
                    color: '#d32f2f',
                    backgroundColor: '#ffebee',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontWeight: 'bold'
                  }}>
                  Delete
                </button>
              </div>
              <div style={{ whiteSpace: 'pre-wrap', fontSize: '14px' }}>
                {trip.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedTrips;
