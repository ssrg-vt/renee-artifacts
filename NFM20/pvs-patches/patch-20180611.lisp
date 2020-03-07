(in-package :pvs)

(defmethod mapping-lhs-theory-context ((thname modname))
  (let ((theory (get-theory thname)))
    (assert theory)
    (unless (every #'typed? (actuals thname))
      (set-type-actuals thname theory))
    (assert (every #'typed? (actuals thname)))
    ;;(assert (null (resolutions thname)))
    (let ((res (resolve* (lcopy thname :mappings nil) 'module nil)))
      (when res
	(assert (null (cdr res)))
	(mapping-lhs-theory-context (declaration (car res)))))))

