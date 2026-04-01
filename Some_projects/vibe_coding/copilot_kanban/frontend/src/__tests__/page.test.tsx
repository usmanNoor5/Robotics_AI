import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Home from '@/app/page';

describe('Kanban Board', () => {
  it('renders columns and initial cards', () => {
    render(<Home />);

    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();

    expect(screen.getByText('Design login flow')).toBeInTheDocument();
    expect(screen.getByText('Set up project scaffold')).toBeInTheDocument();
  });

  it('adds and deletes a card', () => {
    render(<Home />);

    const backlogTitle = screen.getByLabelText('New card title for Backlog');
    fireEvent.change(backlogTitle, { target: { value: 'New test card' } });

    const backlogDetails = screen.getByLabelText('New card details for Backlog');
    fireEvent.change(backlogDetails, { target: { value: 'Detailed text' } });

    const backlogAddButton = screen.getAllByText('+ Add Card')[0];
    fireEvent.click(backlogAddButton);

    expect(screen.getByText('New test card')).toBeInTheDocument();

    const deleteButton = screen.getAllByText('Delete').find((button) =>
      button.closest('article')?.textContent?.includes('New test card')
    );

    expect(deleteButton).toBeDefined();

    if (deleteButton) fireEvent.click(deleteButton);

    expect(screen.queryByText('New test card')).not.toBeInTheDocument();
  });
});
