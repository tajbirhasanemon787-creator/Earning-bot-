import sqlite3,os,logging
from datetime import datetime
logger=logging.getLogger(__name__)
class Database:
 def __init__(self):
  self.conn=sqlite3.connect("earnbot.db",check_same_thread=False)
  self.conn.row_factory=sqlite3.Row
  self._create_tables()
 def _create_tables(self):
  self.conn.executescript('''CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,name TEXT,username TEXT,balance REAL DEFAULT 0,total_earned REAL DEFAULT 0,referrer_id INTEGER,joined_at TEXT);CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,description TEXT,link TEXT,reward REAL,is_active INTEGER DEFAULT 1,created_at TEXT);CREATE TABLE IF NOT EXISTS completed_tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,task_id INTEGER,done_at TEXT,UNIQUE(user_id,task_id));CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,amount REAL,method TEXT,phone TEXT,status TEXT DEFAULT "pending",created_at TEXT);''')
  self.conn.commit()
 def register_user(self,user_id,name,username,referrer_id=None):
  try:
   self.conn.execute("INSERT INTO users(user_id,name,username,referrer_id,joined_at)VALUES(?,?,?,?,?)",(user_id,name,username,referrer_id,datetime.now().isoformat()))
   self.conn.commit()
   return True
  except:return False
 def get_balance(self,uid):
  r=self.conn.execute("SELECT balance FROM users WHERE user_id=?",(uid,)).fetchone()
  return r["balance"]if r else 0.0
 def add_balance(self,uid,amount):
  self.conn.execute("UPDATE users SET balance=balance+?,total_earned=total_earned+? WHERE user_id=?",(amount,amount,uid))
  self.conn.commit()
 def deduct_balance(self,uid,amount):
  self.conn.execute("UPDATE users SET balance=MAX(0,balance-?) WHERE user_id=?",(amount,uid))
  self.conn.commit()
 def get_user_stats(self,uid):
  t=self.conn.execute("SELECT COUNT(*)as c FROM completed_tasks WHERE user_id=?",(uid,)).fetchone()["c"]
  r=self.conn.execute("SELECT COUNT(*)as c FROM users WHERE referrer_id=?",(uid,)).fetchone()["c"]
  w=self.conn.execute("SELECT COALESCE(SUM(amount),0)as s FROM withdrawals WHERE user_id=? AND status='approved'",(uid,)).fetchone()["s"]
  u=self.conn.execute("SELECT total_earned FROM users WHERE user_id=?",(uid,)).fetchone()
  return{"tasks_done":t,"referrals":r,"total_withdrawn":w,"total_earned":u["total_earned"]if u else 0}
 def get_all_users(self):return self.conn.execute("SELECT * FROM users ORDER BY balance DESC").fetchall()
 def get_leaderboard(self,limit=10):return self.conn.execute("SELECT name,total_earned FROM users ORDER BY total_earned DESC LIMIT?",(limit,)).fetchall()
 def add_task(self,title,desc,link,reward):
  cur=self.conn.execute("INSERT INTO tasks(title,description,link,reward,created_at)VALUES(?,?,?,?,?)",(title,desc,link,reward,datetime.now().isoformat()))
  self.conn.commit()
  return cur.lastrowid
 def get_active_tasks(self):return self.conn.execute("SELECT * FROM tasks WHERE is_active=1 ORDER BY id DESC").fetchall()
 def get_task(self,tid):return self.conn.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
 def delete_task(self,tid):
  self.conn.execute("UPDATE tasks SET is_active=0 WHERE id=?",(tid,))
  self.conn.commit()
 def is_task_completed(self,uid,tid):return self.conn.execute("SELECT id FROM completed_tasks WHERE user_id=? AND task_id=?",(uid,tid)).fetchone()is not None
 def complete_task(self,uid,tid):
  try:
   self.conn.execute("INSERT INTO completed_tasks(user_id,task_id,done_at)VALUES(?,?,?)",(uid,tid,datetime.now().isoformat()))
   self.conn.commit()
  except:pass
 def get_completed_count(self,uid):return self.conn.execute("SELECT COUNT(*)as c FROM completed_tasks WHERE user_id=?",(uid,)).fetchone()["c"]
 def create_withdrawal(self,uid,amount,method,phone):
  cur=self.conn.execute("INSERT INTO withdrawals(user_id,amount,method,phone,created_at)VALUES(?,?,?,?,?)",(uid,amount,method,phone,datetime.now().isoformat()))
  self.conn.commit()
  return cur.lastrowid
 def get_pending_withdrawals(self):return self.conn.execute("SELECT w.*,u.name FROM withdrawals w JOIN users u ON w.user_id=u.user_id WHERE w.status='pending' ORDER BY w.id").fetchall()
 def get_withdrawal(self,wid):return self.conn.execute("SELECT * FROM withdrawals WHERE id=?",(wid,)).fetchone()
 def update_withdrawal(self,wid,status):
  self.conn.execute("UPDATE withdrawals SET status=? WHERE id=?",(status,wid))
  self.conn.commit()
 def get_bot_stats(self):
  return{"total_users":self.conn.execute("SELECT COUNT(*)as c FROM users").fetchone()["c"],"tasks_completed":self.conn.execute("SELECT COUNT(*)as c FROM completed_tasks").fetchone()["c"],"total_withdrawn":self.conn.execute("SELECT COALESCE(SUM(amount),0)as s FROM withdrawals WHERE status='approved'").fetchone()["s"],"pending_withdrawals":self.conn.execute("SELECT COUNT(*)as c FROM withdrawals WHERE status='pending'").fetchone()["c"],"active_tasks":self.conn.execute("SELECT COUNT(*)as c FROM tasks WHERE is_active=1").fetchone()["c"]}
