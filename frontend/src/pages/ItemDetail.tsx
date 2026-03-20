import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getItemDetails, updateItemStatus, getItemRewardSettings, updateItemRewardSettings, ItemDetails, RewardSettings } from '../api/frappe'

const ItemDetail = () => {
  const { id } = useParams<{ id: string }>()
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [item, setItem] = useState<ItemDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  const [showStatusMenu, setShowStatusMenu] = useState(false)
  
  // Reward settings state
  const [rewardSettings, setRewardSettings] = useState<RewardSettings | null>(null)
  const [showRewardEdit, setShowRewardEdit] = useState(false)
  const [rewardEnabled, setRewardEnabled] = useState(false)
  const [rewardAmountText, setRewardAmountText] = useState('')
  const [rewardNote, setRewardNote] = useState('')
  const [rewardVisibility, setRewardVisibility] = useState('Public')
  const [isSavingReward, setIsSavingReward] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    if (id) {
      loadItem()
    }
  }, [id])

  const loadItem = async () => {
    setIsLoading(true)
    try {
      const data = await getItemDetails(id!)
      if (data) {
        setItem(data)
        // Also load reward settings
        if (id) {
          try {
            const reward = await getItemRewardSettings(id)
            setRewardSettings(reward)
            setRewardEnabled(reward.reward_enabled)
            setRewardAmountText(reward.reward_amount_text || '')
            setRewardNote(reward.reward_note || '')
            setRewardVisibility(reward.reward_visibility || 'Public')
          } catch (rewardErr) {
            console.error('Failed to load reward settings:', rewardErr)
          }
        }
      } else {
        setError('Item not found or you do not have permission to view it')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load item')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!item) return
    
    setIsUpdating(true)
    try {
      const result = await updateItemStatus(item.id, newStatus)
      if (result.success) {
        setItem({ ...item, status: newStatus })
        setShowStatusMenu(false)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update status')
    } finally {
      setIsUpdating(false)
    }
  }

  const handleSaveReward = async () => {
    if (!item) return
    
    setIsSavingReward(true)
    try {
      const result = await updateItemRewardSettings(
        item.id,
        rewardEnabled,
        rewardEnabled ? rewardAmountText : null,
        rewardEnabled ? rewardNote : null,
        null,
        rewardVisibility
      )
      if (result.success) {
        setShowRewardEdit(false)
        setRewardSettings({
          ...rewardSettings!,
          reward_enabled: rewardEnabled,
          reward_amount_text: rewardAmountText,
          reward_note: rewardNote,
          reward_visibility: rewardVisibility,
        })
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update reward settings')
    } finally {
      setIsSavingReward(false)
    }
  }

  const handleCancelRewardEdit = () => {
    if (rewardSettings) {
      setRewardEnabled(rewardSettings.reward_enabled)
      setRewardAmountText(rewardSettings.reward_amount_text || '')
      setRewardNote(rewardSettings.reward_note || '')
      setRewardVisibility(rewardSettings.reward_visibility || 'Public')
    }
    setShowRewardEdit(false)
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Draft': 'bg-gray-100 text-gray-800',
      'Active': 'bg-green-100 text-green-800',
      'Lost': 'bg-red-100 text-red-800',
      'Recovered': 'bg-blue-100 text-blue-800',
      'Archived': 'bg-yellow-100 text-yellow-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigate('/items')}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  ← Back to Items
                </button>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm text-red-700">{error || 'Item not found'}</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-6">
              <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => navigate('/')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => navigate('/items')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Items
                </button>
                <button
                  onClick={() => navigate('/activate-qr')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Activate QR
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {currentUser as string}
              </span>
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
          <div className="mb-6 flex items-center justify-between">
            <button
              onClick={() => navigate('/items')}
              className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Items
            </button>
            <div className="relative">
              <button
                onClick={() => setShowStatusMenu(!showStatusMenu)}
                disabled={isUpdating}
                className={`inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md ${getStatusBadge(item.status)} hover:opacity-80`}
              >
                {isUpdating ? 'Updating...' : item.status}
                <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showStatusMenu && (
                <div className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg border z-10">
                  {['Active', 'Lost', 'Recovered', 'Archived'].filter(s => s !== item.status).map(status => (
                    <button
                      key={status}
                      onClick={() => handleStatusChange(status)}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Mark as {status}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Item Details</h2>
                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Item Name</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.item_name}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Category</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.item_category_name || '-'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Public Label</dt>
                    <dd className="mt-1 text-sm text-gray-900">{item.public_label || '-'}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                        {item.status}
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>

              <div className="bg-white shadow rounded-xl border p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recovery Information</h2>
                  <button
                    onClick={() => setShowRewardEdit(!showRewardEdit)}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    {showRewardEdit ? 'Cancel' : 'Edit Reward'}
                  </button>
                </div>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Recovery Note</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {item.recovery_note || 'No recovery instructions provided'}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Reward Configuration Section */}
              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Reward Settings</h2>
                
                {!showRewardEdit ? (
                  <dl className="space-y-4">
                    <div className="flex items-center justify-between">
                      <dt className="text-sm font-medium text-gray-500">Reward Enabled</dt>
                      <dd className="mt-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          rewardSettings?.reward_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {rewardSettings?.reward_enabled ? 'Yes' : 'No'}
                        </span>
                      </dd>
                    </div>
                    {rewardSettings?.reward_enabled && (
                      <>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Reward Amount</dt>
                          <dd className="mt-1 text-sm text-gray-900">
                            {rewardSettings.reward_amount_text || '-'}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Reward Note</dt>
                          <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                            {rewardSettings.reward_note || '-'}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Visibility</dt>
                          <dd className="mt-1 text-sm text-gray-900">
                            {rewardSettings.reward_visibility === 'Public' ? 'Public (shown to finders)' : 
                             rewardSettings.reward_visibility === 'Private Mention On Contact' ? 'Private (mention on contact)' : 
                             'Disabled'}
                          </dd>
                        </div>
                      </>
                    )}
                  </dl>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="rewardEnabled"
                        checked={rewardEnabled}
                        onChange={(e) => setRewardEnabled(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                      />
                      <label htmlFor="rewardEnabled" className="ml-2 block text-sm text-gray-900">
                        Enable reward for this item
                      </label>
                    </div>
                    
                    {rewardEnabled && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Reward Amount</label>
                          <input
                            type="text"
                            value={rewardAmountText}
                            onChange={(e) => setRewardAmountText(e.target.value)}
                            placeholder="e.g., ₹500, $50"
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Reward Note</label>
                          <textarea
                            value={rewardNote}
                            onChange={(e) => setRewardNote(e.target.value)}
                            placeholder="Any additional notes about the reward..."
                            rows={3}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Visibility</label>
                          <select
                            value={rewardVisibility}
                            onChange={(e) => setRewardVisibility(e.target.value)}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          >
                            <option value="Public">Public - Show to all finders</option>
                            <option value="Private Mention On Contact">Private - Mention when contacted</option>
                          </select>
                          <p className="mt-1 text-xs text-gray-500">
                            Public: Reward details shown on scan page. Private: Only mentioned when finder contacts you.
                          </p>
                        </div>
                      </>
                    )}
                    
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={handleCancelRewardEdit}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveReward}
                        disabled={isSavingReward || (rewardEnabled && !rewardAmountText)}
                        className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {isSavingReward ? 'Saving...' : 'Save Reward Settings'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {item.photos && item.photos.length > 0 && (
                <div className="bg-white shadow rounded-xl border p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Photos</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {item.photos.map((photo, idx) => (
                      <div key={idx} className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden">
                        {photo.image ? (
                          <img 
                            src={photo.image} 
                            alt={photo.caption || 'Item photo'} 
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full text-gray-400">
                            No image
                          </div>
                        )}
                        {photo.caption && (
                          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1">
                            {photo.caption}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">QR Code</h2>
                {item.qr_code && (
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">QR UID</dt>
                      <dd className="mt-1 text-sm font-mono text-gray-900">{item.qr_code.uid}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Status</dt>
                      <dd className="mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          {item.qr_code.status}
                        </span>
                      </dd>
                    </div>
                  </dl>
                )}
              </div>

              <div className="bg-white shadow rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity</h2>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Activated</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(item.activation_date)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Scan</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(item.last_scan_at)}</dd>
                  </div>
                </dl>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">
                      Founders can scan the QR code to see your recovery notes and contact you.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default ItemDetail