import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useFrappe } from '../api/frappe'

interface ScanifyMeSettings {
  name: string
  site_name: string
  default_privacy_level: 'High' | 'Medium' | 'Low'
  allow_anonymous_messages: boolean
  allow_location_sharing: boolean
  default_reward_message: string
  max_messages_per_hour: number
  max_scans_per_minute: number
}

const Settings = () => {
  const { currentUser, logout } = useAuth()
  const { call } = useFrappe()
  const [settings, setSettings] = useState<ScanifyMeSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const res = await call.get('scanifyme.scanifyme_core.doctype.scanifyme_settings.scanifyme_settings.get_settings')
      setSettings(res.message as ScanifyMeSettings)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!settings) return
    
    setSaving(true)
    setMessage('')
    
    try {
      await call.post('scanifyme.scanifyme_core.doctype.scanifyme_settings.scanifyme_settings.update_settings', settings)
      setMessage('Settings saved successfully')
    } catch (error) {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
            </div>
            <div className="flex items-center space-x-4">
              <a href="/" className="text-sm text-gray-600 hover:text-gray-900">
                Dashboard
              </a>
              <span className="text-sm text-gray-600">
                {currentUser as string}
              </span>
              <a
                href="/app/settings/users"
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                Profile
              </a>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                Settings
              </h2>

              {message && (
                <div className={`mb-4 p-3 rounded ${message.includes('Failed') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                  {message}
                </div>
              )}

              {settings && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Site Name
                    </label>
                    <input
                      type="text"
                      value={settings.site_name}
                      onChange={(e) => setSettings({ ...settings, site_name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Default Privacy Level
                    </label>
                    <select
                      value={settings.default_privacy_level}
                      onChange={(e) => setSettings({ ...settings, default_privacy_level: e.target.value as 'High' | 'Medium' | 'Low' })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.allow_anonymous_messages}
                      onChange={(e) => setSettings({ ...settings, allow_anonymous_messages: e.target.checked })}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900">
                      Allow Anonymous Messages
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.allow_location_sharing}
                      onChange={(e) => setSettings({ ...settings, allow_location_sharing: e.target.checked })}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900">
                      Allow Location Sharing
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Default Reward Message
                    </label>
                    <textarea
                      value={settings.default_reward_message}
                      onChange={(e) => setSettings({ ...settings, default_reward_message: e.target.value })}
                      rows={3}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Max Messages Per Hour
                    </label>
                    <input
                      type="number"
                      value={settings.max_messages_per_hour}
                      onChange={(e) => setSettings({ ...settings, max_messages_per_hour: parseInt(e.target.value) })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Max Scans Per Minute
                    </label>
                    <input
                      type="number"
                      value={settings.max_scans_per_minute}
                      onChange={(e) => setSettings({ ...settings, max_scans_per_minute: parseInt(e.target.value) })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>

                  <div>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Settings
