import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { activateQR, createItem, getItemCategories, ItemCategory } from '../api/frappe'

const ActivateQR = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [qrCode, setQrCode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [activationResult, setActivationResult] = useState<any>(null)
  const [itemName, setItemName] = useState('')
  const [itemCategory, setItemCategory] = useState('')
  const [recoveryNote, setRecoveryNote] = useState('')
  const [rewardNote, setRewardNote] = useState('')
  const [categories, setCategories] = useState<ItemCategory[]>([])
  const [isCreating, setIsCreating] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setActivationResult(null)

    if (!qrCode.trim()) {
      setError('Please enter a QR code token')
      return
    }

    setIsLoading(true)

    try {
      const result = await activateQR(qrCode.trim())
      setActivationResult(result)
      
      if (result.needs_item_creation) {
        const cats = await getItemCategories()
        setCategories(cats)
      } else if (result.linked_item) {
        setSuccess(`This QR code is already linked to item: ${result.linked_item_name}`)
        setTimeout(() => navigate(`/items/${result.linked_item}`), 2000)
      }
    } catch (err: any) {
      // Map error messages to user-friendly versions
      const errorMsg = err?.message || ''
      if (errorMsg.includes('Invalid QR token') || errorMsg.includes('not found')) {
        setError('This token is not recognized. Please check the token on your QR tag.')
      } else if (errorMsg.includes('already activated') || errorMsg.includes('already linked')) {
        setError('This QR code has already been activated.')
      } else if (errorMsg.includes('cannot be activated') || errorMsg.includes('Suspended') || errorMsg.includes('Retired')) {
        setError('This QR code cannot be activated. It may be suspended or retired. Please contact support.')
      } else {
        setError(errorMsg || 'Failed to activate QR code. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsCreating(true)

    if (!itemName.trim()) {
      setError('Please enter an item name')
      setIsCreating(false)
      return
    }

    try {
      const item = await createItem({
        item_name: itemName.trim(),
        qr_code_tag: activationResult.qr_tag.name,
        item_category: itemCategory || undefined,
        recovery_note: recoveryNote || undefined,
        reward_note: rewardNote || undefined,
      })
      
      setSuccess('Item created successfully!')
      setTimeout(() => navigate(`/items/${item}`), 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to create item')
    } finally {
      setIsCreating(false)
    }
  }

  const handleReset = () => {
    setQrCode('')
    setActivationResult(null)
    setItemName('')
    setItemCategory('')
    setRecoveryNote('')
    setRewardNote('')
    setError('')
    setSuccess('')
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
                  className="text-indigo-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
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
          {!activationResult ? (
            <div className="max-w-xl mx-auto">
              <div className="bg-white shadow rounded-xl border">
                <div className="p-6">
                  <div className="text-center mb-6">
                    <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-indigo-100">
                      <svg
                        className="h-8 w-8 text-indigo-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h2M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
                        />
                      </svg>
                    </div>
                    <h1 className="mt-4 text-2xl font-bold text-gray-900">
                      Activate QR Code
                    </h1>
                    <p className="mt-2 text-sm text-gray-500">
                      Enter the QR code token to associate it with an item
                    </p>
                  </div>

                  {/* Activation Help Card */}
                  <div className="bg-blue-50 border border-blue-200 rounded-xl mb-6 p-4">
                    <h3 className="text-sm font-semibold text-blue-900 mb-2">How QR Activation Works</h3>
                    <div className="text-xs text-blue-700 space-y-1">
                      <p>1. Find the token on your QR tag or in the QR packaging</p>
                      <p>2. Enter the token above and click "Activate QR Code"</p>
                      <p>3. Fill in your item details to complete registration</p>
                    </div>
                    <p className="text-xs text-blue-600 mt-2">
                      Tokens are typically 8-10 characters (e.g., "DNEEYP5TLQ")
                    </p>
                  </div>

                  <form onSubmit={handleActivate} className="space-y-4">
                    <div>
                      <label
                        htmlFor="qr-token"
                        className="block text-sm font-medium text-gray-700"
                      >
                        QR Token
                      </label>
                      <input
                        type="text"
                        id="qr-token"
                        value={qrCode}
                        onChange={(e) => setQrCode(e.target.value.toUpperCase())}
                        placeholder="e.g., X7K9M4PQ"
                        className="mt-1 block w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono"
                        maxLength={12}
                      />
                      <p className="mt-2 text-xs text-gray-500">
                        Found on the QR code or QR batch documentation
                      </p>
                    </div>

                    {error && (
                      <div className="rounded-md bg-red-50 p-4">
                        <div className="flex">
                          <svg
                            className="h-5 w-5 text-red-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <div className="ml-3">
                            <p className="text-sm text-red-700">{error}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {success && (
                      <div className="rounded-md bg-green-50 p-4">
                        <div className="flex">
                          <svg
                            className="h-5 w-5 text-green-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          <div className="ml-3">
                            <p className="text-sm text-green-700">{success}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? (
                        <svg
                          className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          ></path>
                        </svg>
                      ) : null}
                      {isLoading ? 'Activating...' : 'Activate QR Code'}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          ) : activationResult.needs_item_creation ? (
            <div className="max-w-xl mx-auto">
              <div className="bg-white shadow rounded-xl border">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="text-center flex-1">
                      <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                        <svg
                          className="h-6 w-6 text-green-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                      <h2 className="mt-3 text-lg font-semibold text-gray-900">
                        QR Code Activated
                      </h2>
                      <p className="mt-1 text-sm text-gray-500">
                        UID: {activationResult.qr_tag.qr_uid}
                      </p>
                    </div>
                    <button
                      onClick={handleReset}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Change
                    </button>
                  </div>

                  <form onSubmit={handleCreateItem} className="space-y-4">
                    <div>
                      <label
                        htmlFor="item-name"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Item Name *
                      </label>
                      <input
                        type="text"
                        id="item-name"
                        value={itemName}
                        onChange={(e) => setItemName(e.target.value)}
                        placeholder="e.g., My Bicycle"
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="item-category"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Category
                      </label>
                      <select
                        id="item-category"
                        value={itemCategory}
                        onChange={(e) => setItemCategory(e.target.value)}
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      >
                        <option value="">Select a category</option>
                        {categories.map((cat) => (
                          <option key={cat.name} value={cat.name}>
                            {cat.category_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor="recovery-note"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Recovery Note
                      </label>
                      <textarea
                        id="recovery-note"
                        value={recoveryNote}
                        onChange={(e) => setRecoveryNote(e.target.value)}
                        placeholder="Instructions for finders on how to return this item..."
                        rows={3}
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="reward-note"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Reward Note
                      </label>
                      <textarea
                        id="reward-note"
                        value={rewardNote}
                        onChange={(e) => setRewardNote(e.target.value)}
                        placeholder="Reward information for finders..."
                        rows={2}
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      />
                    </div>

                    {error && (
                      <div className="rounded-md bg-red-50 p-4">
                        <div className="flex">
                          <svg
                            className="h-5 w-5 text-red-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <div className="ml-3">
                            <p className="text-sm text-red-700">{error}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {success && (
                      <div className="rounded-md bg-green-50 p-4">
                        <div className="flex">
                          <svg
                            className="h-5 w-5 text-green-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          <div className="ml-3">
                            <p className="text-sm text-green-700">{success}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={handleReset}
                        className="flex-1 py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isCreating}
                        className="flex-1 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isCreating ? 'Creating...' : 'Create Item'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  )
}

export default ActivateQR
