import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../../App'
import { AppProviders } from '../providers'

describe('App Shell', () => {
  const renderApp = () => {
    return render(
      <AppProviders>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </AppProviders>
    )
  }

  it('shows the Genonaut brand and default dashboard page', () => {
    renderApp()

    expect(screen.getByRole('banner')).toHaveTextContent(/genonaut/i)
    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1, name: /welcome back/i })).toBeInTheDocument()
  })
})
